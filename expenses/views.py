from .seralizers import LoginSerializer, SignupSerializer, ExpensesSerializer, CategoriesSerializer
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import response
from rest_framework.views import APIView
from .models import Expenses, Categories
from django.contrib.auth import login
from django.db.models import F, Sum, Count, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
# Create your views here.

@method_decorator(never_cache, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self,request):
        return render(request, 'expenses/login.html')
    
    def post(self, request):
        seralizer = LoginSerializer(data=request.data)
        if seralizer.is_valid():
            login(request, seralizer.validated_data['user'])
            return redirect('dashboard')
    
        else:
            errors = {'errors': seralizer.errors}
            return render(request, 'expenses/login.html', errors)

class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(never_cache, name='dispatch')
    def get(self, request):
        return render(request, 'expenses/signup.html')
    
    def post(self, request):
        seralizer = SignupSerializer(data=request.data)
        
        if seralizer.is_valid():
            seralizer.save()
            return redirect('login') 
        else:
            return render(request, 'expenses/signup.html', {'errors': seralizer.errors, 'values': request.POST})
        
class DashboardAPIView(APIView):
    # We remove the global permission here to handle it manually for display login page when go user to dashboard directly without login.
    permission_classes = []
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        
        now = timezone.now().date()
        expenses_current_month = Expenses.objects.select_related('category').filter(user=request.user, date__year = now.year, date__month = now.month).order_by('-date')
        current_month_total = expenses_current_month.aggregate(Sum('amount'))['amount__sum'] or 0

        last_day_in_last_month = now.replace(day=1) - timedelta(days=1)
        first_day_in_last_month = last_day_in_last_month.replace(day=1)
        expenses_last_month = Expenses.objects.filter(user=request.user, date__gte=first_day_in_last_month, date__lte=last_day_in_last_month)
        previous_month_total = expenses_last_month.aggregate(Sum('amount'))['amount__sum'] or 0

        monthly_spending_diff = current_month_total - previous_month_total

        if previous_month_total > 0:
            spending_change_percent = round (((current_month_total - previous_month_total) / previous_month_total) * 100, 2)
        else :
            spending_change_percent = 0

        user_salary = request.user.salary or 0

        budget_remaining = user_salary - current_month_total

        if user_salary > 0:
            budget_used = round((current_month_total / user_salary) * 100, 2)
        else:
            budget_used = 0

        user_categories = expenses_current_month.values(name=F('category__name'), color=F('category__color')).annotate(total=Sum('amount')).order_by('-total')

        categories_summary = []

        for entry in user_categories: 
            name =  entry['name']
            color = entry['color']
            amount = entry['total']
            ratio = round((float(entry['total']) / float(current_month_total)) * 100, 2) if current_month_total else 0

            categories_summary.append({
                'name': name,
                'color': color,
                'amount': amount,
                'ratio': ratio,
            })

        content = {
            'today': now.strftime("%b %d"),
            'expenses': expenses_current_month,
            'current_month_total': current_month_total,
            'previous_month_total': previous_month_total,
            'monthly_spending_diff': monthly_spending_diff,
            'spending_change_percent': spending_change_percent,
            'budget_remaining': budget_remaining,
            'budget_used': budget_used,
            'categories':categories_summary, 
        }
        return render(request, 'expenses/dashboard.html', content)
    
class ExpensesAPIView(APIView):
    def get(self, request, pk = None):        
        expenses_queryset = Expenses.objects.filter(user=request.user).order_by('-date')
        
        selected_month = request.GET.get('date')
        selected_category = request.GET.get('category') 
        if selected_month:
            year, month = selected_month.split('-')
            expenses_queryset = expenses_queryset.filter(
                date__year=year,
                date__month=month,
            )
        if selected_category:
            expenses_queryset = expenses_queryset.filter(
                category_id=selected_category,
            )
        total_spent = expenses_queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        
        categories = Categories.objects.filter(user=request.user)
        content = {
            'total_spent': total_spent,
            'categories': categories,
            'expenses': expenses_queryset,
        }
        return render(request, 'expenses/expenses.html', content) 

    def post(self, request):
        expense = get_object_or_404(
            Expenses,
            pk=request.data.get('expense_id'),
            user=request.user,
        )
        action = request.data.get('action')

        if action == 'delete':
            expense.delete()
            return redirect('expenses')

        if action == 'edit':
            serializer = ExpensesSerializer(
                expense,
                data=request.data,
                context={'request': request},
            )
            if serializer.is_valid():
                serializer.save()
                return redirect('expenses')

            expenses_queryset = Expenses.objects.filter(user=request.user).order_by('-date')
            return render(request, 'expenses/expenses.html', {
                'total_spent': expenses_queryset.aggregate(Sum('amount'))['amount__sum'] or 0,
                'categories': Categories.objects.filter(user=request.user),
                'expenses': expenses_queryset,
                'edit_expense_id': expense.id,
                'edit_errors': serializer.errors,
                'edit_values': request.POST,
            }, status=400)

        return redirect('expenses')
    
class AddExpenseAPIView(APIView):
    def get(self, request):
        categories = Categories.objects.filter(user=request.user)
        content = {'categories': categories}
        return render(request, 'expenses/add-expense.html', content)
    
    def post(self, request):
        serializer = ExpensesSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return redirect('expenses')
        
        categories = Categories.objects.filter(user=request.user)

        return render(request, 'expenses/add-expense.html', {
            'errors': serializer.errors,
            'values': request.POST,
            'categories': categories,
        })

class CategoriesAPIView(APIView):
    def get_categories(self, request):
        now = timezone.now().date()
        return Categories.objects.filter(user=request.user).annotate(
            total_expenses = Coalesce(
                    Sum('expenses__amount',filter=Q(expenses__date__year=now.year, expenses__date__month=now.month)), 
                    Value(Decimal(0.0))
            ),
            num_expenses = Coalesce(
                    Count('expenses__id',filter=Q(expenses__date__year=now.year, expenses__date__month=now.month)), 
                    Value(0)
            )
        ).values('id', 'name', 'color', 'total_expenses', 'num_expenses')

    def get(self, request):
        return render(request, 'expenses/categories.html', {
            'expenses_per_category': self.get_categories(request),
        })

    def post(self, request):
        action = request.data.get('action')

        if action == 'delete':
            category = get_object_or_404(
                Categories,
                pk=request.data.get('category_id'),
                user=request.user,
            )
            category.delete()
            return redirect('categories')

        category = None
        if action == 'edit':
            category = get_object_or_404(
                Categories,
                pk=request.data.get('category_id'),
                user=request.user,
            )

        if action in ('add', 'edit'):
            serializer = CategoriesSerializer(
                category,
                data=request.data,
                context={'request': request},
            )
            if serializer.is_valid():
                serializer.save()
                return redirect('categories')

            return render(request, 'expenses/categories.html', {
                'expenses_per_category': self.get_categories(request),
                'category_form_action': action,
                'edit_category_id': category.id if category else None,
                'category_errors': serializer.errors,
                'category_values': request.POST,
            }, status=400)

        return redirect('categories')

class ReportsAPIView(APIView):
    def get(self, request):
        return render(request, 'expenses/reports.html')
    
    # def post(self, request):
    #     serializer = ExpensesAPIView(data=request.data)
    #     serializer.save()
