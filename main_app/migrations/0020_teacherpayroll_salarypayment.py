from django.db import migrations, models
import django.db.models.deletion


def seed_demo_accounts(apps, schema_editor):
    Staff = apps.get_model("main_app", "Staff")
    TeacherPayrollProfile = apps.get_model("main_app", "TeacherPayrollProfile")
    for staff_id in Staff.objects.values_list("pk", flat=True).iterator():
        TeacherPayrollProfile.objects.get_or_create(
            staff_id=staff_id,
            defaults={"bank_name": "Velocity Demo Bank", "account_number": f"VTU-DEMO-{staff_id:06d}"},
        )


class Migration(migrations.Migration):

    dependencies = [("main_app", "0019_portalaccesssettings")]

    operations = [
        migrations.CreateModel(
            name="TeacherPayrollProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bank_name", models.CharField(default="Velocity Demo Bank", max_length=80)),
                ("account_number", models.CharField(max_length=40, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("staff", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payroll_profile", to="main_app.staff")),
            ],
        ),
        migrations.CreateModel(
            name="SalaryPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pay_period", models.CharField(help_text="YYYY-MM", max_length=7)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=11)),
                ("account_number", models.CharField(max_length=40)),
                ("status", models.CharField(choices=[("pending", "Pending approval"), ("paid", "Paid (demo)"), ("rejected", "Rejected")], default="pending", max_length=10)),
                ("payment_reference", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_salary_payments", to="main_app.customuser")),
                ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="salary_payments", to="main_app.staff")),
            ],
            options={"ordering": ("-pay_period", "staff__admin__first_name", "staff__admin__last_name")},
        ),
        migrations.AddConstraint(
            model_name="salarypayment",
            constraint=models.UniqueConstraint(fields=("staff", "pay_period"), name="unique_salary_payment_per_teacher_period"),
        ),
        migrations.RunPython(seed_demo_accounts, migrations.RunPython.noop),
    ]
