from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
# Create your models here.
class User(AbstractUser):
    salary = models.DecimalField(
        max_digits=13, 
        decimal_places=2,  
        default=0
    )

    def __str__(self):
        return self.username
    
class Categories(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7, 
        default='#52b788'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories'
    )

    class Meta():
        constraints = [models.UniqueConstraint(
            fields=['name', 'user'],
            name='unique_category_per_user'
        )]

    def __str__(self):
        return self.name

class Expenses(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='expenses'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(
            Decimal('0.01'),
            message="Amount must be at least 0.01."
        )]
    )
    date = models.DateField()
    description = models.TextField(
        blank=True, 
        null=True
    ) 
    category = models.ForeignKey(
        Categories, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} : {self.description}"
    
class UserReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.user.username} ({self.start_date} to {self.end_date})"