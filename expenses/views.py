from rest_framework.views import APIView
from django.shortcuts import render, redirect
from .seralizers import LoginSerializer
# Create your views here.

class LoginAPIView(APIView):
    def get(self,request):
        return render(request, 'expenses/login.html')
    
    def post(self, request):
        seralizer = LoginSerializer(data = request.data)

        if seralizer.is_valid():

            pass
        else:
            return render(request, 'expenses/login.html', seralizer.errors)

class SignupAPIView(APIView):
    def get(self, request):
        return render(request, 'expenses/signup.html')