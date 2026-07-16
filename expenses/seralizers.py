from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Category, Expense


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        error_messages={"blank": "Please enter your username."},
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={"blank": "Please enter your password."},
    )

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                "Username or password is incorrect."
            )

        attrs["user"] = user
        return attrs


class SignupSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(
        write_only=True,
        error_messages={"blank": "Please enter your password confirmation."},
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "password_confirm",
        ]
        extra_kwargs = {
            "first_name": {
                "required": True,
                "allow_blank": False,
                "error_messages": {"blank": "Please enter your first name."},
            },
            "last_name": {
                "required": True,
                "allow_blank": False,
                "error_messages": {"blank": "Please enter your last name."},
            },
            "username": {
                "error_messages": {
                    "blank": "Please enter your username.",
                    "unique": "That username is already taken.",
                }
            },
            "email": {
                "required": True,
                "allow_blank": False,
                "error_messages": {"blank": "Please enter your email."},
            },
            "password": {
                "write_only": True,
                "error_messages": {"blank": "Please enter your password."},
            },
        }

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class ExpensesSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    date = serializers.DateField(format="%b %d")

    class Meta:
        model = Expense
        fields = [
            "user",
            "description",
            "amount",
            "date",
            "category",
            "category_name",
            "category_color",
            "created_at",
            "updated_at",
        ]

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "The expense date cannot be in the future."
            )
        return value

    def validate_category(self, value):
        request_user = self.context["request"].user
        if value and value.user_id != request_user.id:
            raise serializers.ValidationError(
                "Please select one of your categories."
            )
        return value


class CategoriesSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Category
        fields = ["user", "name", "color"]

    def validate_name(self, value):
        value = value.strip()
        queryset = Category.objects.filter(
            user=self.context["request"].user,
            name__iexact=value,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "You already have a category with this name."
            )
        return value
