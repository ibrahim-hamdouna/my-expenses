from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import login
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Category, Expense
from .report_exports import create_excel_report, create_pdf_report
from .seralizers import (
    CategoriesSerializer,
    ExpensesSerializer,
    LoginSerializer,
    SignupSerializer,
)


ZERO_AMOUNT = Decimal("0.00")


def expense_list_context(user, expenses=None):
    if expenses is None:
        expenses = Expense.objects.filter(user=user).order_by("-date")

    return {
        "total_spent": expenses.aggregate(total=Sum("amount"))["total"]
        or ZERO_AMOUNT,
        "categories": Category.objects.filter(user=user).order_by("name"),
        "expenses": expenses,
    }


@method_decorator(never_cache, name="dispatch")
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, "expenses/login.html")

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            login(request, serializer.validated_data["user"])
            return redirect("dashboard")

        return render(
            request,
            "expenses/login.html",
            {"errors": serializer.errors},
            status=400,
        )


@method_decorator(never_cache, name="dispatch")
class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, "expenses/signup.html")

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect("login")

        return render(
            request,
            "expenses/signup.html",
            {"errors": serializer.errors, "values": request.POST},
            status=400,
        )


class DashboardAPIView(APIView):
    # This view redirects anonymous users instead of returning DRF's 403 response.
    permission_classes = []

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        today = timezone.localdate()
        current_expenses = (
            Expense.objects.select_related("category")
            .filter(user=request.user, date__year=today.year, date__month=today.month)
            .order_by("-date")
        )
        current_total = (
            current_expenses.aggregate(total=Sum("amount"))["total"] or ZERO_AMOUNT
        )

        previous_month_end = today.replace(day=1) - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        previous_total = (
            Expense.objects.filter(
                user=request.user,
                date__range=(previous_month_start, previous_month_end),
            ).aggregate(total=Sum("amount"))["total"]
            or ZERO_AMOUNT
        )

        spending_difference = current_total - previous_total
        spending_change_percent = (
            round(spending_difference / previous_total * 100, 2)
            if previous_total
            else Decimal("0")
        )

        salary = request.user.salary or ZERO_AMOUNT
        budget_remaining = salary - current_total
        budget_used = (
            round(current_total / salary * 100, 2) if salary else Decimal("0")
        )

        category_totals = (
            current_expenses.values(
                name=F("category__name"),
                color=F("category__color"),
            )
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        categories = [
            {
                "name": entry["name"] or "No category",
                "color": entry["color"] or "#6B7280",
                "amount": entry["total"],
                "ratio": (
                    round(entry["total"] / current_total * 100, 2)
                    if current_total
                    else Decimal("0")
                ),
            }
            for entry in category_totals
        ]

        return render(
            request,
            "expenses/dashboard.html",
            {
                "today": today.strftime("%b %d"),
                "expenses": current_expenses,
                "current_month_total": current_total,
                "previous_month_total": previous_total,
                "monthly_spending_diff": spending_difference,
                "spending_change_percent": spending_change_percent,
                "budget_remaining": budget_remaining,
                "budget_used": budget_used,
                "categories": categories,
            },
        )


class ExpensesAPIView(APIView):
    def get(self, request):
        expenses = Expense.objects.filter(user=request.user).order_by("-date")

        selected_month = request.GET.get("date", "")
        month = parse_date(f"{selected_month}-01") if selected_month else None
        if month:
            expenses = expenses.filter(date__year=month.year, date__month=month.month)

        selected_category = request.GET.get("category", "")
        if selected_category.isdigit():
            expenses = expenses.filter(category_id=selected_category)

        return render(
            request,
            "expenses/expenses.html",
            expense_list_context(request.user, expenses),
        )

    def post(self, request):
        action = request.data.get("action")
        if action not in {"delete", "edit"}:
            return redirect("expenses")

        expense = get_object_or_404(
            Expense,
            pk=request.data.get("expense_id"),
            user=request.user,
        )
        if action == "delete":
            expense.delete()
            return redirect("expenses")

        serializer = ExpensesSerializer(
            expense,
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return redirect("expenses")

        context = expense_list_context(request.user)
        context.update(
            {
                "edit_expense_id": expense.id,
                "edit_errors": serializer.errors,
                "edit_values": request.POST,
            }
        )
        return render(
            request,
            "expenses/expenses.html",
            context,
            status=400,
        )


class AddExpenseAPIView(APIView):
    def get(self, request):
        return render(
            request,
            "expenses/add-expense.html",
            {"categories": Category.objects.filter(user=request.user).order_by("name")},
        )

    def post(self, request):
        serializer = ExpensesSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return redirect("expenses")

        return render(
            request,
            "expenses/add-expense.html",
            {
                "errors": serializer.errors,
                "values": request.POST,
                "categories": Category.objects.filter(user=request.user).order_by(
                    "name"
                ),
            },
            status=400,
        )


class CategoriesAPIView(APIView):
    @staticmethod
    def get_categories(user):
        today = timezone.localdate()
        current_month = Q(
            expenses__date__year=today.year,
            expenses__date__month=today.month,
        )
        return (
            Category.objects.filter(user=user)
            .annotate(
                total_expenses=Coalesce(
                    Sum("expenses__amount", filter=current_month),
                    Value(ZERO_AMOUNT),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
                num_expenses=Count("expenses", filter=current_month),
            )
            .values("id", "name", "color", "total_expenses", "num_expenses")
            .order_by("name")
        )

    def get(self, request):
        return render(
            request,
            "expenses/categories.html",
            {"expenses_per_category": self.get_categories(request.user)},
        )

    def post(self, request):
        action = request.data.get("action")
        if action not in {"add", "edit", "delete"}:
            return redirect("categories")

        category = None
        if action in {"edit", "delete"}:
            category = get_object_or_404(
                Category,
                pk=request.data.get("category_id"),
                user=request.user,
            )

        if action == "delete":
            category.delete()
            return redirect("categories")

        serializer = CategoriesSerializer(
            category,
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return redirect("categories")

        return render(
            request,
            "expenses/categories.html",
            {
                "expenses_per_category": self.get_categories(request.user),
                "category_form_action": action,
                "edit_category_id": category.id if category else None,
                "category_errors": serializer.errors,
                "category_values": request.POST,
            },
            status=400,
        )


class ReportsAPIView(APIView):
    def get(self, request):
        categories = Category.objects.filter(user=request.user).order_by("name")
        expenses = (
            Expense.objects.select_related("category")
            .filter(user=request.user)
            .order_by("-date")
        )

        start_value = request.GET.get("start_date", "")
        end_value = request.GET.get("end_date", "")
        category_value = request.GET.get("category", "")
        start_date = parse_date(start_value) if start_value else None
        end_date = parse_date(end_value) if end_value else None
        errors = []

        if start_value and not start_date:
            errors.append("Please enter a valid start date.")
        if end_value and not end_date:
            errors.append("Please enter a valid end date.")
        if start_date and end_date and start_date > end_date:
            errors.append("The start date cannot be after the end date.")

        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        if category_value:
            if category_value.isdigit() and categories.filter(
                pk=category_value
            ).exists():
                expenses = expenses.filter(category_id=category_value)
            else:
                errors.append("Please select one of your categories.")

        total = expenses.aggregate(total=Sum("amount"))["total"] or ZERO_AMOUNT
        export_format = request.GET.get("export")
        if export_format in {"pdf", "excel"} and not errors:
            return self.export_report(
                export_format,
                list(expenses),
                total,
                start_date,
                end_date,
            )

        return render(
            request,
            "expenses/reports.html",
            {
                "expenses": expenses,
                "categories": categories,
                "total": total,
                "errors": errors,
                "selected_start_date": start_value,
                "selected_end_date": end_value,
                "selected_category": category_value,
            },
            status=400 if errors else 200,
        )

    @staticmethod
    def export_report(
        export_format,
        expenses,
        total,
        start_date,
        end_date,
    ):
        filename = f"expenses-report-{timezone.localdate()}"
        if export_format == "pdf":
            content = create_pdf_report(
                expenses,
                total,
                start_date,
                end_date,
            )
            content_type = "application/pdf"
            extension = "pdf"
        else:
            content = create_excel_report(expenses, total)
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            extension = "xlsx"

        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}.{extension}"'
        )
        return response
