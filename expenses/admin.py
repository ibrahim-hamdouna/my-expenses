from .models import User , Category, Expenses, UserReport
from django.contrib import admin
# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Expenses)
admin.site.register(UserReport)