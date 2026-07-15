from django.contrib.auth import authenticate, get_user_model
from .models import Expenses, Categories, UserReport
from rest_framework import serializers   
from django.utils import timezone
User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        error_messages={
            'blank': 'Please enter your username.'
        }
    )
    password = serializers.CharField(
        write_only=True, 
        required=True,
        error_messages={
            'blank': 'Please enter your password.'
        }
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username = username, password = password)
        
        if user is None:
            raise serializers.ValidationError("Username or password is incorrect.")
        
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
    category_name = serializers.StringRelatedField(
        source='category.name',
        read_only=True,
        allow_null=True,
    )
    category_color = serializers.StringRelatedField(
        source='category.color',
        read_only=True,
        allow_null=True,
    )
    date = serializers.DateField(format="%b %d")
    class Meta:
        model = Expenses
        fields = ['description', 'amount',  'date', 'category', 'category_name', 'category_color', 'created_at', 'updated_at']
    
    def create(self, validate_data):
        validate_data['user'] = self.context['request'].user
        return super().create(validate_data)
    
    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("The expense date cannot be in the future.")
        return value

    def validate_category(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("Please select one of your categories.")
        return value

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['name', 'color']

    def validate_name(self, value):
        queryset = Categories.objects.filter(
            user=self.context['request'].user,
            name__iexact=value.strip(),
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("You already have a category with this name.")
        return value.strip()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = ['user', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):    
        current_user = self.context['request'].user
        validated_data['user'] = current_user
        return UserReport.objects.create(**validated_data)
