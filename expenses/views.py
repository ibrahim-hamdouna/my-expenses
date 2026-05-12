from .seralizers import LoginSerializer, SignupSerializer, ExpensesSerializer, CategorySerializer
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from .models import Expenses, Category
from django.contrib.auth import login
from django.db.models import F, Sum
from django.utils import timezone
from datetime import timedelta
# Create your views here.

class LoginAPIView(APIView):
    def get(self,request):
        return render(request, 'expenses/login.html')
    
    def post(self, request):
        seralizer = LoginSerializer(data=request.data)
        if seralizer.is_valid():
            login(request, seralizer.validated_data['user'])
            return  redirect('dashboard')
    
        else:
            errors = {'errors': seralizer.errors}
            return render(request, 'expenses/login.html', errors)

class SignupAPIView(APIView):
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
    def get(self, request):

        now = timezone.now().date()
        current_month = now.month
        expenses_queryset_for_current_month = Expenses.objects.select_related('category').filter(user=request.user, date__month = current_month).order_by('-date')
        current_month_total = expenses_queryset_for_current_month.aggregate(Sum('amount'))['amount__sum'] or 0

        last_day_in_last_month = now.replace(day=1) - timedelta(days=1)
        first_day_in_last_month = last_day_in_last_month.replace(day=1)
        expenses_queryset_for_last_month = Expenses.objects.filter(user=request.user, date__gte=first_day_in_last_month, date__lte=last_day_in_last_month)
        previous_month_total = expenses_queryset_for_last_month.aggregate(Sum('amount'))['amount__sum'] or 0

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

        user_categories = expenses_queryset_for_current_month.values(name=F('category__name'), color=F('category__color')).annotate(total=Sum('amount')).order_by('-total')

        serializer_expenses_for_current_month = ExpensesSerializer(expenses_queryset_for_current_month, many=True)

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
            'expenses': serializer_expenses_for_current_month.data,
            'current_month_total': current_month_total,
            'previous_month_total': previous_month_total,
            'monthly_spending_diff': monthly_spending_diff,
            'spending_change_percent': spending_change_percent,
            'budget_remaining': budget_remaining,
            'budget_used': budget_used,
            'categorys':categories_summary, 
        }
        return render(request, 'expenses/dashboard.html', content)
    
class ExpensesAPIView(APIView):
    def get(self, request):
        expenses_queryset = Expenses.objects.filter(user=request.user)
        # total_spent = expenses_queryset.aaggregate(Sum('amount'))['amount__sum'] or 0
        expenses_serializer = ExpensesSerializer(expenses_queryset, many=True)
        
        categories_queryset = Category.objects.filter(user=request.user)
        categories_serializer = CategorySerializer(categories_queryset, many=True)
        content = {
            'expenses': expenses_serializer.data,
            'categories': categories_serializer.data,
            # 'total_spent': total_spent,
        }
        return render(request, 'expenses/expenses.html', content)     

class ReportsAPIView(APIView):
    def get(self, request):
        return render(request, 'expenses/reports.html')
    
    # def post(self, request):
    #     serializer = ExpensesAPIView(data=request.data)
    #     serializer.save()