from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

# Create your models here.
class User(AbstractUser):
    salary = models.DecimalField(
        max_digits=13, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return self.username
class Category(models.Model):
    name = models.CharField(max_length=100)
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
    title = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    ) 
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"