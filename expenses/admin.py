from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Expense, User, UserReport


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (*UserAdmin.list_display, "is_active", "salary")
    fieldsets = (*UserAdmin.fieldsets, ("Financial information", {"fields": ("salary",)}))
    add_fieldsets = (*UserAdmin.add_fieldsets, ("Financial information", {"fields": ("salary",)}))
    list_editable = ("is_active", "salary")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "user")
    list_filter = ("user",)
    search_fields = ("name", "user__username")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "date", "category")
    list_filter = ("date", "category")
    search_fields = ("user__username", "description")
    date_hierarchy = "date"


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("user", "start_date", "end_date", "created_at")
    list_filter = ("start_date", "end_date")
    search_fields = ("user__username",)
