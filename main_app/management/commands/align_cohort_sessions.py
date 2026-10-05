from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main_app.models import (
    Attendance, Course, CourseRegistration, FeeStructure, Session, Staff, Student,
    Subject,
)


CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "brainware_catalog.json"
AI_ML_COURSE = (
    "Bachelor of Technology in Computer Science & Engineering - "
    "Artificial Intelligence & Machine Learning"
)


def duration_years(value: str) -> int | None:
    match = re.search(r"(\d+)", str(value or ""))
    return int(match.group(1)) if match else None


def due_date(start_year: int, semester_number: int) -> date:
    if semester_number % 2:
        return date(start_year + (semester_number - 1) // 2, 8, 31)
    return date(start_year + semester_number // 2, 1, 31)


class Command(BaseCommand):
    help = "Align academic sessions through 2030 and apply exact Semester 7 teacher assignments from 7J.pdf."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write session, fee schedule, and teacher assignment changes.")

    def handle(self, *args, **options):
        try:
            catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read academic catalog: {exc}") from exc

        catalog_courses = {row["course_name"]: row for row in catalog["courses"]}
        lateral_rows = {row["Course Name"]: row for row in catalog.get("lateral", [])}
        course_rows = {course.name: course for course in Course.objects.filter(name__in=catalog_courses)}
        if set(catalog_courses) - set(course_rows):
            raise CommandError("The workbook courses are not fully loaded. Import the workbook catalog before aligning sessions.")

        target_keys = {
            (start_year, years)
            for start_year in range(2023, 2031)
            for years in (2, 3, 4)
        }
        target_count = len(target_keys)
        expected_fees = 0
        for course_name, row in catalog_courses.items():
            years = duration_years(row.get("duration"))
            if years not in (2, 3, 4):
                continue
            semester_count = int(row.get("total_semesters") or 0)
            expected_fees += semester_count * sum(1 for _, cohort_years in target_keys if cohort_years == years)
            lateral_row = lateral_rows.get(course_name, {})
            if years == 4 and str(row.get("Lateral Entry Applicable", "")).strip().lower() == "yes":
                expected_fees += sum(
                    1 for number in range(3, semester_count + 1)
                    if lateral_row.get(f"Semester {number} Fee") is not None
                ) * sum(1 for _, cohort_years in target_keys if cohort_years == 4)

        self.stdout.write(
            f"Plan: {target_count} session cohorts (2023-2030 start years, durations 2/3/4), "
            f"about {expected_fees} active workbook fee rows, existing accounts and payment records preserved."
        )
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Run with --apply to update the database."))
            return

        with transaction.atomic():
            canonical = {}
            for start_year, years in sorted(target_keys):
                start_date = date(start_year, 7, 1)
                end_date = date(start_year + years, 6, 30)
                session, _ = Session.objects.get_or_create(
                    start_year=start_date,
                    end_year=end_date,
                )
                canonical[(start_year, years)] = session

            def session_for(start_year: int, years: int):
                if years not in (2, 3, 4):
                    return None
                cohort_year = min(max(start_year, 2023), 2030)
                return canonical[(cohort_year, years)]

            changed_students = []
            for student in Student.objects.select_related("course", "session"):
                if student.session_id and student.course_id:
                    target = session_for(student.session.start_year.year, duration_years(student.course.duration))
                    if target and student.session_id != target.pk:
                        student.session = target
                        changed_students.append(student)
            Student.objects.bulk_update(changed_students, ("session",), batch_size=200)

            changed_registrations = []
            for registration in CourseRegistration.objects.select_related("course", "session"):
                if registration.session_id:
                    target = session_for(registration.session.start_year.year, duration_years(registration.course.duration))
                    if target and registration.session_id != target.pk:
                        registration.session = target
                        changed_registrations.append(registration)
            CourseRegistration.objects.bulk_update(changed_registrations, ("session",), batch_size=200)

            changed_attendance = []
            for record in Attendance.objects.select_related("session", "subject__course"):
                if record.session_id and record.subject_id:
                    target = session_for(record.session.start_year.year, duration_years(record.subject.course.duration))
                    if target and record.session_id != target.pk:
                        record.session = target
                        changed_attendance.append(record)
            Attendance.objects.bulk_update(changed_attendance, ("session",), batch_size=200)

            # Lateral students use the standard four-year cohort session, while
            # retaining their separate fee rows and admission-type flag.
            fee_rows = list(FeeStructure.objects.select_related("course", "session", "semester"))
            for fee in fee_rows:
                if not fee.session_id:
                    continue
                years = 4 if fee.entry_type == FeeStructure.EntryType.LATERAL else duration_years(fee.course.duration)
                target = session_for(fee.session.start_year.year, years)
                if target and fee.session_id != target.pk:
                    fee.session = target
                if fee.entry_type == FeeStructure.EntryType.LATERAL and "(Lateral Entry)" not in fee.title:
                    fee.title = f"{fee.title[:95]} (Lateral Entry)"
            FeeStructure.objects.bulk_update(fee_rows, ("session", "title"), batch_size=200)

            target_session_ids = {session.pk for session in canonical.values()}
            for old_session in Session.objects.exclude(pk__in=target_session_ids):
                if (Student.objects.filter(session=old_session).exists()
                        or CourseRegistration.objects.filter(session=old_session).exists()
                        or Attendance.objects.filter(session=old_session).exists()
                        or FeeStructure.objects.filter(session=old_session).exists()):
                    raise CommandError(f"Could not safely remove nonstandard session {old_session}; an academic record still uses it.")
                old_session.delete()

            # Fill missing schedules for every workbook course/cohort, without
            # deleting any payment records attached to existing fee items.
            existing = list(FeeStructure.objects.select_related("course", "session", "semester"))
            by_key = {
                (fee.course_id, fee.session_id, fee.semester_id, fee.entry_type): fee
                for fee in existing if fee.session_id and fee.semester_id
            }
            to_create = []
            to_update = []
            for course_name, row in catalog_courses.items():
                course = course_rows[course_name]
                years = duration_years(row.get("duration"))
                if years not in (2, 3, 4):
                    continue
                semesters = {sem.number: sem for sem in course.semesters.all()}
                cohorts = [canonical[(start_year, years)] for start_year in range(2023, 2031)]
                for cohort in cohorts:
                    for number in range(1, int(row.get("total_semesters") or 0) + 1):
                        amount = row.get(f"sem_{number}_fee_inr")
                        semester = semesters.get(number)
                        if amount is None or semester is None:
                            continue
                        key = (course.pk, cohort.pk, semester.pk, FeeStructure.EntryType.REGULAR)
                        fee = by_key.get(key)
                        values = {
                            "session": cohort, "semester": semester,
                            "title": f"Semester {number} Tuition",
                            "amount": Decimal(str(amount)), "due_date": due_date(cohort.start_year.year, number),
                            "is_active": True,
                        }
                        if fee:
                            for field, value in values.items():
                                setattr(fee, field, value)
                            to_update.append(fee)
                        else:
                            to_create.append(FeeStructure(
                                course=course, entry_type=FeeStructure.EntryType.REGULAR, **values,
                            ))
                lateral = lateral_rows.get(course_name, {})
                if years == 4 and course.lateral_entry_applicable:
                    for cohort in (canonical[(start_year, 4)] for start_year in range(2023, 2031)):
                        for number in range(course.lateral_entry_semester or 3, course.total_semesters + 1):
                            amount = lateral.get(f"Semester {number} Fee")
                            semester = semesters.get(number)
                            if amount is None or semester is None:
                                continue
                            key = (course.pk, cohort.pk, semester.pk, FeeStructure.EntryType.LATERAL)
                            fee = by_key.get(key)
                            values = {
                                "session": cohort, "semester": semester,
                                "title": f"Semester {number} Tuition (Lateral Entry)",
                                "amount": Decimal(str(amount)), "due_date": due_date(cohort.start_year.year, number),
                                "is_active": True,
                            }
                            if fee:
                                for field, value in values.items():
                                    setattr(fee, field, value)
                                to_update.append(fee)
                            else:
                                to_create.append(FeeStructure(
                                    course=course, entry_type=FeeStructure.EntryType.LATERAL, **values,
                                ))
            FeeStructure.objects.bulk_update(
                list({fee.pk: fee for fee in to_update}.values()),
                ("session", "semester", "title", "amount", "due_date", "is_active"), batch_size=200,
            )
            FeeStructure.objects.bulk_create(to_create, batch_size=200)

            course = course_rows[AI_ML_COURSE]
            teachers = {
                email: Staff.objects.filter(admin__email__iexact=email).first()
                for email in (
                    "poulomi@gmail.com", "keya@gmail.com", "sudipta@gmail.com",
                    "deepayan@gmail.com", "dipanjan@gmail.com", "sharmistha@gmail.com",
                    "sabyasachi@gmail.com",
                )
            }
            assignments = (
                ("poulomi@gmail.com", "OEC-CSM702", "Soft Skills and Interpersonal Communication"),
                ("dipanjan@gmail.com", "OEC-CSM701", "AI with Robotics"),
                ("deepayan@gmail.com", "PCC-CSM701", "Software Engineering"),
                ("sudipta@gmail.com", "PEC-CSM701", "Deep Learning"),
                ("sharmistha@gmail.com", "PEC-CSM702", "Introduction to Data Analytics and Visualization"),
                ("deepayan@gmail.com", "PCC-CSM791", "Software Tools and Techniques Lab"),
            )
            assigned_count = 0
            not_found = []
            for email, code, title in assignments:
                teacher = teachers.get(email)
                subject = Subject.objects.filter(
                    course=course, semester__number=7, code__iexact=code,
                    name__icontains=title,
                ).first()
                if teacher is None or subject is None:
                    not_found.append(f"{email}: {code} {title}")
                    continue
                if subject.staff_id != teacher.pk:
                    subject.staff = teacher
                    subject.save(update_fields=("staff", "updated_at"))
                assigned_count += 1
            lab = Subject.objects.filter(
                course=course, semester__number=7, code__iexact="PCC-CSM791",
                name__icontains="Software Tools and Techniques Lab",
            ).first()
            lab_co_teacher = teachers.get("sudipta@gmail.com")
            if lab and lab_co_teacher and lab.staff_id != lab_co_teacher.pk:
                lab.co_teachers.add(lab_co_teacher)

        self.stdout.write(self.style.SUCCESS(
            f"Updated {Session.objects.count()} standard sessions, preserved {Student.objects.count()} student accounts, "
            f"{Staff.objects.count()} teacher accounts and all payment records; confirmed {assigned_count} PDF-based subject assignments."
        ))
        self.stdout.write(f"Active fee schedule rows: {FeeStructure.objects.filter(is_active=True).count()}")
        self.stdout.write("Not assigned from this timetable: Keya Hazra's APT-701 (not present in the uploaded curriculum), and Sabyasachi Chandra's TBC class (subject not identified).")
        if not_found:
            self.stdout.write(self.style.WARNING("Some exact code/title matches need manual review: " + "; ".join(not_found)))
