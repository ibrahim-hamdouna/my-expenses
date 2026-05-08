from .seralizers import LoginSerializer, SignupSerializer, ExpensesSerializer, CategorySerializer
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from .models import Expenses, Category
from django.contrib.auth import login
from django.db.models import F, Sum
from django.utils import timezone
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

        expenses_queryset = Expenses.objects.select_related('category').filter(user=request.user, date__month = current_month)

        total_spent = expenses_queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        user_salary = request.user.salary or 0
        budget_remaining = user_salary - total_spent

        user_categories = expenses_queryset.values(name=F('category__name')).annotate(total=Sum('amount')).order_by('-total')

        serializer_expenses = ExpensesSerializer(expenses_queryset, many=True)

        categories_summary = []

        for entry in user_categories: 
            name =  entry['name']
            amount = entry['total']
            ratio = round((float(entry['total']) / float(total_spent)) * 100, 2) if total_spent else 0

            categories_summary.append({
                'name': name,
                'amount': amount,
                'ratio': ratio,
            })

        content = {
            'today': now.strftime("%b %d"),
            'expenses': serializer_expenses.data,
            'total_spent': total_spent,
            'budget_remaining': budget_remaining,
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