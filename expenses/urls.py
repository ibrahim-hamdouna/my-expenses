from .views import LoginAPIView, SignupAPIView
from django.urls import path

urlpatterns = [
    path('', LoginAPIView().as_view, name='login'),
    path('signup/', SignupAPIView.as_view, name='signup')
]


