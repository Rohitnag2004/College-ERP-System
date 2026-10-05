from django.db import migrations


def remove_unused_generic_courses(apps, schema_editor):
    Course = apps.get_model("main_app", "Course")
    Staff = apps.get_model("main_app", "Staff")
    Student = apps.get_model("main_app", "Student")
    Subject = apps.get_model("main_app", "Subject")
    CourseRegistration = apps.get_model("main_app", "CourseRegistration")
    FeeStructure = apps.get_model("main_app", "FeeStructure")

    legacy = Course.objects.filter(name__in=("Python", "C", "Java"))
    for course in legacy:
        has_academic_records = (
            Student.objects.filter(course_id=course.pk).exists()
            or Subject.objects.filter(course_id=course.pk).exists()
            or CourseRegistration.objects.filter(course_id=course.pk).exists()
            or FeeStructure.objects.filter(course_id=course.pk).exists()
        )
        if has_academic_records:
            course.is_active = False
            course.save(update_fields=("is_active",))
            continue
        Staff.objects.filter(course_id=course.pk).update(course=None)
        course.delete()


class Migration(migrations.Migration):
    dependencies = [("main_app", "0004_brainware_course_catalog")]

    operations = [migrations.RunPython(remove_unused_generic_courses, migrations.RunPython.noop)]
