from django.db import migrations


def disable_estimates(apps, schema_editor):
    FeeStructure = apps.get_model("main_app", "FeeStructure")
    FeeStructure.objects.filter(title__contains="planning estimate").update(is_active=False)


def restore_estimates(apps, schema_editor):
    FeeStructure = apps.get_model("main_app", "FeeStructure")
    FeeStructure.objects.filter(title__contains="planning estimate").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("main_app", "0007_seed_semester_plan")]
    operations = [migrations.RunPython(disable_estimates, restore_estimates)]
