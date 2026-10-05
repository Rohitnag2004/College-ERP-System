import re
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


AI_ML_SUBJECTS = [
    ["Engineering Mathematics I", "Physics for Computing", "Programming in C", "Digital Logic Design", "Communication Skills", "Environmental Studies"],
    ["Engineering Mathematics II", "Data Structures", "Object-Oriented Programming", "Computer Organization", "Discrete Mathematics", "Python Programming"],
    ["Probability and Statistics", "Database Management Systems", "Design and Analysis of Algorithms", "Operating Systems", "Data Communication and Networks", "Foundations of Artificial Intelligence"],
    ["Linear Algebra for Machine Learning", "Software Engineering", "Theory of Computation", "Computer Networks", "Machine Learning I", "Data Engineering Fundamentals"],
    ["Deep Learning", "Natural Language Processing", "Computer Vision", "Cloud Computing", "Machine Learning Lab", "Responsible AI and Ethics"],
    ["Reinforcement Learning", "Big Data Analytics", "Generative AI Fundamentals", "MLOps and Model Deployment", "AI Research Methods", "Elective I"],
    ["Advanced Deep Learning", "AI Product Design", "AI Security and Privacy", "Elective II", "Industry Internship / Project I", "Seminar"],
    ["Capstone Project", "AI Systems Engineering", "Technology Entrepreneurship", "Elective III", "Professional Practice", "Project Viva"],
]


def seed(apps, schema_editor):
    Course = apps.get_model("main_app", "Course")
    Session = apps.get_model("main_app", "Session")
    Student = apps.get_model("main_app", "Student")
    Semester = apps.get_model("main_app", "Semester")
    Subject = apps.get_model("main_app", "Subject")
    FeeStructure = apps.get_model("main_app", "FeeStructure")
    AttendanceReport = apps.get_model("main_app", "AttendanceReport")

    AttendanceReport.objects.filter(status=True).update(attendance_status="present")
    AttendanceReport.objects.filter(status=False).update(attendance_status="absent")

    session, _ = Session.objects.get_or_create(
        start_year=date(2026, 7, 1), end_year=date(2027, 6, 30)
    )
    Student.objects.filter(session__isnull=True, course__isnull=False).update(session=session)

    courses = list(Course.objects.all())
    semester_rows = []
    fee_specs = []
    for course in courses:
        durations = [int(value) for value in re.findall(r"(\d+)\s*year", course.duration.lower())]
        years = max(durations) if durations else 4
        if "3-4 years" in course.duration.lower():
            years = 4
        count = max(2, years * 2)
        total = None
        if course.tuition_fee_min is not None and course.tuition_fee_max is not None:
            total = (Decimal(course.tuition_fee_min) + Decimal(course.tuition_fee_max)) / Decimal(2)
        elif course.tuition_fee_min is not None:
            total = Decimal(course.tuition_fee_min)
        elif course.tuition_fee_max is not None:
            total = Decimal(course.tuition_fee_max)
        base = (total / count).quantize(Decimal("100"), rounding=ROUND_HALF_UP) if total else Decimal("0")
        remainder = total - base * (count - 1) if total else Decimal("0")
        for number in range(1, count + 1):
            amount = remainder if number == count else base
            semester_rows.append(Semester(
                course_id=course.pk, number=number, name=f"Semester {number}", fee_estimate=amount,
            ))
            fee_specs.append((course.pk, number, amount))

    Semester.objects.bulk_create(semester_rows, batch_size=500)
    semester_ids = {
        (row.course_id, row.number): row.pk
        for row in Semester.objects.only("id", "course_id", "number")
    }
    FeeStructure.objects.bulk_create([
        FeeStructure(
            course_id=course_id, session_id=None, semester_id=semester_ids[(course_id, number)],
            title=f"Semester {number} Tuition (planning estimate)", amount=amount,
            due_date=date(2026, 10, 1) + timedelta(days=183 * (number - 1)), is_active=True,
        )
        for course_id, number, amount in fee_specs
    ], batch_size=500)

    subject_rows = []
    for course in courses:
        if "artificial intelligence & machine learning" in course.name.lower() and course.name.lower().startswith("b.tech"):
            for number, names in enumerate(AI_ML_SUBJECTS, start=1):
                semester_id = semester_ids[(course.pk, number)]
                subject_rows.extend(
                    Subject(name=name, course_id=course.pk, semester_id=semester_id)
                    for name in names
                )
    Subject.objects.bulk_create(subject_rows, batch_size=200, ignore_conflicts=True)


def unseed(apps, schema_editor):
    Session = apps.get_model("main_app", "Session")
    Semester = apps.get_model("main_app", "Semester")
    FeeStructure = apps.get_model("main_app", "FeeStructure")
    Course = apps.get_model("main_app", "Course")
    FeeStructure.objects.filter(title__contains="planning estimate").delete()
    Semester.objects.all().delete()
    Session.objects.filter(start_year=date(2026, 7, 1), end_year=date(2027, 6, 30)).delete()


class Migration(migrations.Migration):
    dependencies = [("main_app", "0006_semester_teacher_attendance")]
    operations = [migrations.RunPython(seed, unseed)]
