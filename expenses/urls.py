from .views import (
    LoginAPIView, 
    SignupAPIView, 
    DashboardAPIView, 
    ExpensesAPIView, 
    AddExpenseAPIView, 
    CategoriesAPIView, 
    ReportsAPIView,
)
from django.urls import path

urlpatterns = [
    path('', LoginAPIView().as_view(), name='login'),
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('expenses/', ExpensesAPIView.as_view(), name='expenses'),
    path('add-expense/', AddExpenseAPIView.as_view(), name='add-expense'),
    path('categories/', CategoriesAPIView.as_view(), name='categories'),
    path('reports/', ReportsAPIView.as_view(), name='reports'),
]


