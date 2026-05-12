from django.contrib.auth import authenticate, get_user_model
from .models import Expenses, Category, UserReport
from rest_framework import serializers   

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username:
            raise serializers.ValidationError("Please enter your username.")
        
        if not password:
            raise serializers.ValidationError("Please enter your password.")

        user = authenticate(username = username, password = password)

        if not user:
            raise serializers.ValidationError("Username or password is incorrect.")
        
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        
        data['user'] = user
        
        return data
    
class SignupSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'blank': 'Please enter your password confirmation.'
        }
    )
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username","email", "password", "password_confirm"]
        extra_kwargs = {
            'first_name': {
                'required': True, 
                'allow_blank': False,
                'error_messages':{
                    'blank': 'Please enter your first name.'
                }
            },
            'last_name': {
                'required': True, 
                'allow_blank': False,
                'error_messages':{
                    'blank': 'Please enter your last name.'
                }
            },
            'username': {
                'error_messages':{
                    'blank': "Please enter your username",
                    'unique': 'That username is already taken'
                }
            },
            'email': {
                'required': True,
                'allow_blank': False,
                'error_messages':{
                    'blank': "Please enter your email"                
                }
            },
            'password' : {
                'write_only': True,
                'error_messages':{
                    'blank': "Please enter your password",
                }
            } 
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

class ExpensesSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(source='category.name')
    category_color = serializers.StringRelatedField(source='category.color')
    date = serializers.DateField(format="%b %d")
    class Meta:
        model = Expenses
        fields = ['description', 'amount',  'date', 'category_name', 'category_color', 'created_at', 'updated_at']
    
    def create(self, validate_data):
        user = self.context['request'].user
        validate_data['user'] = user
        return super().create(**validate_data)
    
    # def validate(self, attrs):
    #     return super().validate(attrs)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'color', 'user']

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = ['user', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):    
        current_user = self.context['request'].user
        validated_data['user'] = current_user
        return UserReport.objects.create(**validated_data)