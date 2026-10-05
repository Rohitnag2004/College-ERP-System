from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def seed_sessions_and_reweight(apps, schema_editor):
    Session = apps.get_model("main_app", "Session")
    Course = apps.get_model("main_app", "Course")
    Semester = apps.get_model("main_app", "Semester")
    FeeStructure = apps.get_model("main_app", "FeeStructure")
    FeePayment = apps.get_model("main_app", "FeePayment")

    for start_year in range(2022, 2026):
        Session.objects.get_or_create(
            start_year=date(start_year, 7, 1),
            end_year=date(start_year + 1, 6, 30),
        )

    courses = list(Course.objects.all())
    semesters_by_course = {}
    all_semesters = list(Semester.objects.all().order_by("course_id", "number"))
    for semester in all_semesters:
        semesters_by_course.setdefault(semester.course_id, []).append(semester)
    all_fees = list(FeeStructure.objects.filter(title__contains="planning estimate"))
    fees_by_semester = {fee.semester_id: fee for fee in all_fees}
    protected_fee_ids = set(FeePayment.objects.filter(
        fee_id__in=[fee.pk for fee in all_fees], status__in=("paid", "pending")
    ).values_list("fee_id", flat=True))
    semesters_to_update = []
    fees_to_update = []

    for course in courses:
        semesters = semesters_by_course.get(course.pk, [])
        if not semesters:
            continue
        fees = [fees_by_semester[row.pk] for row in semesters if row.pk in fees_by_semester]
        if any(fee.pk in protected_fee_ids for fee in fees):
            continue
        if course.tuition_fee_min is not None and course.tuition_fee_max is not None:
            total = (Decimal(course.tuition_fee_min) + Decimal(course.tuition_fee_max)) / Decimal(2)
        elif course.tuition_fee_min is not None:
            total = Decimal(course.tuition_fee_min)
        elif course.tuition_fee_max is not None:
            total = Decimal(course.tuition_fee_max)
        else:
            total = sum((Decimal(fee.amount) for fee in fees), Decimal("0"))

        count = len(semesters)
        weight_total = Decimal(count * (count + 1) // 2)
        amounts = []
        remaining = total
        for index, semester in enumerate(semesters):
            if index == count - 1:
                amount = remaining
            else:
                weight = Decimal(count - index)
                amount = (total * weight / weight_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                remaining -= amount
            amounts.append(amount)
            semester.fee_estimate = amount
        for index, semester in enumerate(semesters):
            semesters_to_update.append(semester)
            fee = fees_by_semester.get(semester.pk)
            if fee:
                fee.amount = amounts[index]
                fees_to_update.append(fee)

    Semester.objects.bulk_update(semesters_to_update, ["fee_estimate"], batch_size=500)
    FeeStructure.objects.bulk_update(fees_to_update, ["amount"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("main_app", "0009_remove_gateway_payment_fields")]
    operations = [migrations.RunPython(seed_sessions_and_reweight, migrations.RunPython.noop)]
