import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


def replace_null_descriptions(apps, schema_editor):
    Expense = apps.get_model("expenses", "Expense")
    Expense.objects.filter(description__isnull=True).update(description="")


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0007_alter_expenses_amount"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Categories",
            new_name="Category",
        ),
        migrations.RenameModel(
            old_name="Expenses",
            new_name="Expense",
        ),
        migrations.RunPython(
            replace_null_descriptions,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="category",
            name="color",
            field=models.CharField(
                default="#52b788",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a color in #RRGGBB format.",
                        regex="^#[0-9A-Fa-f]{6}$",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="expense",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="expenses",
                to="expenses.category",
            ),
        ),
        migrations.AlterField(
            model_name="expense",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="salary",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=13,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AlterField(
            model_name="userreport",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="userreport",
            constraint=models.CheckConstraint(
                condition=models.Q(start_date__lte=models.F("end_date")),
                name="report_start_date_lte_end_date",
            ),
        ),
    ]
