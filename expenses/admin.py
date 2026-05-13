from .models import User , Categories, Expenses, UserReport
from django.contrib import admin
# Register your models here.

admin.site.register(User)
admin.site.register(Categories)
admin.site.register(Expenses)
admin.site.register(UserReport)