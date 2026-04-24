from django.urls import path
from .views import LoginAPIView

urlpatterns = [
    path('', LoginAPIView().as_view, name='login'),
]