from rest_framework import serializers   
from django.contrib.auth import authenticate, get_user_model
from .models import Expenses, Category, UserReport

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password :
            user = authenticate(username = username, password = password)

            if not user:
                raise serializers.ValidationError("Username or password is incorrect.")

        else:
            raise serializers.ValidationError('Must include username and password.')
        
        data['user'] = user
        
        return data
    
class SignupSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username","email", "password", "password_confirm"]
        extra_kwargs = {
            'first_name': {
                'required': True, 
                'allow_blank': False
            },
            'last_name': {
                'required': True, 
                'allow_blank': False
            },
            'username': {
                'error_messages':{
                    'unique': 'That username is already taken'
                }
            },
            'password' : {
                'write_only': True
            },
            'password_confirm' : {
                'write_only': True
            }
            
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_date):
        validated_date.pop('password_confirm')
        return User.objects.create_user(**validated_date)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'user']

class ExpensesSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(many=True)
    class Meta:
        model = Expenses
        fields = ['title', 'amount', 'date', 'category_name', 'description', 'created_at', 'updated_at']
    

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = ['user', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):    
        current_user = self.context['request'].user
        validated_data['user'] = current_user
        return UserReport.objects.create(**validated_data)