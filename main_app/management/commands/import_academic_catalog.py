from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from django.utils import timezone
from pathlib import Path
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main_app.models import (
    Attendance, AttendanceReport, CollegeResource, Course, CourseRegistration, FeePayment,
    FeeStructure, Semester, Session, Staff, Student, StudentResult, Subject,
)

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "brainware_catalog.json"


def normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def catalog_subject_key(name, catalog_subject_names):
    normalized = normalize(name)
    matches = [
        (alias, canonical) for alias, canonical in catalog_subject_names.items()
        if normalized == alias or normalized.endswith(" " + alias)
    ]
    return max(matches, key=lambda pair: len(pair[0]))[1] if matches else None


def target_for_course(name, catalog_names):
    """Map legacy catalog labels to an unambiguous workbook course, else leave unset."""
    value = normalize(name)
    exact = {normalize(item): item for item in catalog_names}
    if value in exact:
        return exact[value]
    is_master = any(token in value for token in ("master", "m tech", "mca", "m sc"))
    if "diploma" in value:
        if "electrical" in value:
            return next((n for n in catalog_names if "Diploma in Electrical" in n), None)
        if "mechanical" in value:
            return next((n for n in catalog_names if "Diploma in Mechanical" in n), None)
        if "computer science" in value or "cse" in value:
            return next((n for n in catalog_names if "Diploma in Computer Science" in n), None)
    if "computer applications" in value or "bca" in value or "mca" in value:
        return next((n for n in catalog_names if ("Master of Computer Applications" in n) if is_master), None) if is_master else next((n for n in catalog_names if "Bachelor of Computer Applications" in n), None)
    if "advanced networking" in value or "cyber security" in value:
        if is_master:
            return next((n for n in catalog_names if "Master of Science" in n and "Advanced Networking" in n), None)
        return next((n for n in catalog_names if "Bachelor of Science" in n and "Advanced Networking" in n), None)
    if is_master and ("robot" in value or "automation" in value):
        return next((n for n in catalog_names if "Master of Technology" in n and "Robotics" in n), None)
    if is_master and ("artificial intelligence" in value or "ai ml" in value or "computer science" in value):
        return next((n for n in catalog_names if "Master of Technology" in n and "Artificial Intelligence" in n), None)
    if not is_master and ("b tech" in value or "bachelor of technology" in value):
        if "artificial intelligence" in value or "ai ml" in value:
            return next((n for n in catalog_names if "Bachelor of Technology" in n and "Artificial Intelligence" in n), None)
        return next((n for n in catalog_names if "Bachelor of Technology" in n and "Computer Science" in n and "Artificial Intelligence" not in n), None)
    return None


def years_from_duration(value):
    match = re.search(r"(\d+)", str(value or ""))
    return int(match.group(1)) if match else None


def semester_due_date(base_year, semester_number):
    if semester_number % 2:
        year = base_year + (semester_number - 1) // 2
        return date(year, 8, 31)
    year = base_year + semester_number // 2
    return date(year, 1, 31)


class Command(BaseCommand):
    help = "Replace the academic catalog from the supplied workbook data while preserving all user accounts."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report the catalog plan without writing changes (default).")
        parser.add_argument("--replace", action="store_true", help="Replace old academic catalog/history while preserving user accounts.")

    def handle(self, *args, **options):
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read bundled workbook data: {exc}") from exc

        courses = data.get("courses", [])
        curriculum = data.get("curriculum", [])
        lateral = {row["Course Name"]: row for row in data.get("lateral", [])}
        if not courses or len({row["course_name"] for row in courses}) != len(courses):
            raise CommandError("Workbook catalog is empty or contains duplicate course names.")
        course_names = [row["course_name"] for row in courses]
        subject_names = {}
        for row in curriculum:
            full_name = normalize(row.get("subject_name"))
            subject_names[full_name] = full_name
            if ":" in str(row.get("subject_name") or ""):
                suffix = normalize(str(row["subject_name"]).split(":", 1)[1])
                if suffix:
                    subject_names[suffix] = full_name
        for row in curriculum:
            if row.get("course_name") not in set(course_names):
                raise CommandError(f"Curriculum references an unknown course: {row.get('course_name')}")

        if options["dry_run"] or not options["replace"]:
            self.stdout.write(self.style.WARNING(
                f"Dry run: {len(courses)} courses, {len(curriculum)} subjects, "
                f"{sum(int(row.get('total_semesters') or 0) for row in courses)} regular semesters. "
                "No database records changed. To replace old academic data, run with --replace; "
                "admin/student/teacher accounts are preserved."
            ))
            return

        current_names = set(Course.objects.values_list("name", flat=True))
        current_subject_count = Subject.objects.count()
        current_coded_count = Subject.objects.exclude(code="").count()
        if current_names == set(course_names) and current_subject_count == len(curriculum) and current_coded_count == len(curriculum):
            self.stdout.write(self.style.SUCCESS("Workbook catalog is already loaded; skipped to protect activity recorded since the import."))
            return

        with transaction.atomic():
            # Capture user assignments and teacher-to-subject assignments before replacing catalog rows.
            student_assignments = []
            for student in Student.objects.select_related("course", "semester"):
                old_name = student.course.name if student.course_id else ""
                student_assignments.append((student, target_for_course(old_name, course_names), student.semester.number if student.semester_id else None, "lateral" if "lateral entry" in normalize(old_name) else student.admission_type))
            staff_assignments = []
            for staff in Staff.objects.select_related("course"):
                old_name = staff.course.name if staff.course_id else ""
                staff_assignments.append((staff, target_for_course(old_name, course_names)))
            teacher_by_subject = defaultdict(list)
            old_assigned_subject_count = Subject.objects.filter(staff__isnull=False).count()
            for subject in Subject.objects.select_related("course", "semester", "staff"):
                if not subject.staff_id or not subject.semester_id:
                    continue
                target_name = target_for_course(subject.course.name, course_names)
                if target_name:
                    subject_key = catalog_subject_key(subject.name, subject_names)
                    if subject_key:
                        teacher_by_subject[(target_name, subject.semester.number, subject_key)].append(subject.staff_id)

            resource_assignments = []
            for resource in CollegeResource.objects.select_related("course", "semester", "subject"):
                old_course_name = resource.course.name if resource.course_id else ""
                target_name = target_for_course(old_course_name, course_names)
                old_semester_number = resource.semester.number if resource.semester_id else None
                subject_name = catalog_subject_key(resource.subject.name, subject_names) if resource.subject_id else ""
                resource_assignments.append((resource, target_name, old_semester_number, subject_name))

            # The request replaces old academic data. Keep user identities, credentials and roles intact.
            FeePayment.objects.all().delete()
            FeeStructure.objects.all().delete()
            CourseRegistration.objects.all().delete()
            AttendanceReport.objects.all().delete()
            Attendance.objects.all().delete()
            StudentResult.objects.all().delete()
            Subject.objects.all().delete()
            Semester.objects.all().delete()
            Student.objects.update(course=None, semester=None)
            Staff.objects.update(course=None)
            Course.objects.all().delete()

            course_rows_to_create = []
            course_rows_by_name = {}
            for row in courses:
                lateral_row = lateral.get(row["course_name"], {})
                lat_semester = lateral_row.get("Admission Semester")
                lat_match = re.search(r"(\d+)", str(lat_semester or ""))
                obj = Course(
                    name=row["course_name"],
                    description=f"{row.get('degree_level') or ''} · {row.get('duration') or ''}".strip(" ·"),
                    degree_level=row.get("degree_level") or "",
                    entry_type=row.get("entry_type") or "",
                    syllabus_year=int(row["syllabus_year"]) if row.get("syllabus_year") else None,
                    duration=row.get("duration") or "",
                    total_semesters=int(row.get("total_semesters") or 0),
                    total_fee=Decimal(str(row["total_fee_inr"])) if row.get("total_fee_inr") is not None else None,
                    fee_source_status=row.get("fee_source_status") or "",
                    lateral_entry_applicable=str(row.get("Lateral Entry Applicable", "")).strip().lower() == "yes",
                    lateral_entry_admission_year=row.get("Lateral Entry Admission Year") or "",
                    lateral_entry_semester=int(lat_match.group(1)) if lat_match else None,
                    lateral_entry_continuation=row.get("Lateral Entry Continuation") or "",
                    lateral_entry_duration=lateral_row.get("Duration After Lateral Entry") or "",
                    lateral_entry_total_fee=Decimal(str(lateral_row["Fee Total (2026-27)"])) if lateral_row.get("Fee Total (2026-27)") is not None else None,
                    tuition_fee_min=Decimal(str(row["total_fee_inr"])) if row.get("total_fee_inr") is not None else None,
                    tuition_fee_max=Decimal(str(row["total_fee_inr"])) if row.get("total_fee_inr") is not None else None,
                    is_active=True,
                )
                course_rows_to_create.append(obj)
                course_rows_by_name[obj.name] = (obj, row)
            Course.objects.bulk_create(course_rows_to_create, batch_size=100)
            course_objects = {obj.name: obj for obj in course_rows_to_create}

            semester_rows_to_create = []
            for name, (course, row) in course_rows_by_name.items():
                for number in range(1, course.total_semesters + 1):
                    amount = row.get(f"sem_{number}_fee_inr")
                    if amount is not None:
                        semester_rows_to_create.append(Semester(
                            course=course, number=number, name=f"Semester {number}",
                            fee_estimate=Decimal(str(amount)), is_active=True,
                        ))
            Semester.objects.bulk_create(semester_rows_to_create, batch_size=200)
            semester_objects = {(item.course.name, item.number): item for item in semester_rows_to_create}

            subjects_to_create = []
            for row in curriculum:
                course = course_objects[row["course_name"]]
                try:
                    number = int(row["semester"])
                except (TypeError, ValueError):
                    continue
                semester = semester_objects.get((course.name, number))
                if semester is None:
                    continue
                normalized_name = normalize(row.get("subject_name"))
                teacher_ids = teacher_by_subject.get((course.name, number, normalized_name), [])
                subjects_to_create.append(Subject(
                    name=row["subject_name"], code=str(row.get("subject_code") or ""),
                    subject_type=str(row.get("subject_type") or ""),
                    syllabus_year=int(row["syllabus_year"]) if row.get("syllabus_year") else None,
                    source=str(row.get("source") or ""), course=course, semester=semester,
                    staff_id=teacher_ids[0] if teacher_ids else None,
                ))
            Subject.objects.bulk_create(subjects_to_create, batch_size=500)
            subjects_by_key = {}
            for subject in Subject.objects.select_related("semester"):
                if subject.semester_id:
                    subjects_by_key.setdefault((subject.course.name, subject.semester.number, normalize(subject.name)), subject)
            for resource, course_name, semester_number, subject_name in resource_assignments:
                if not course_name:
                    continue
                resource.course = course_objects[course_name]
                resource.semester = semester_objects.get((course_name, semester_number)) if semester_number else None
                resource.subject = subjects_by_key.get((course_name, semester_number, subject_name)) if semester_number and subject_name else None
            if resource_assignments:
                CollegeResource.objects.bulk_update([row[0] for row in resource_assignments if row[1]], ("course", "semester", "subject"), batch_size=200)

            mapped_students = 0
            registrations_to_create = []
            for student, course_name, number, admission_type in student_assignments:
                course = course_objects.get(course_name)
                student.course = course
                student.semester = semester_objects.get((course_name, number)) if course and number else None
                student.admission_type = admission_type if admission_type in ("regular", "lateral") else Student.EntryType.REGULAR
                if course:
                    mapped_students += 1
                    registrations_to_create.append(CourseRegistration(
                        student=student, course=course, session=student.session,
                        status=CourseRegistration.Status.APPROVED,
                        reviewed_at=timezone.now(),
                        admin_note="Enrollment restored from the existing student assignment during the workbook catalog refresh.",
                    ))
            if student_assignments:
                Student.objects.bulk_update([row[0] for row in student_assignments], ("course", "semester", "admission_type"), batch_size=200)
            CourseRegistration.objects.bulk_create(registrations_to_create, batch_size=200)

            for staff, course_name in staff_assignments:
                staff.course = course_objects.get(course_name)
            if staff_assignments:
                Staff.objects.bulk_update([row[0] for row in staff_assignments], ("course",), batch_size=200)

            # Fee figures are the workbook's 2026-27 chart. Apply them to the currently configured sessions.
            sessions = list(Session.objects.order_by("start_year"))
            fee_rows_to_create = []
            for row in courses:
                course = course_objects[row["course_name"]]
                regular_years = years_from_duration(course.duration)
                regular_sessions = [session for session in sessions if session.end_year.year - session.start_year.year == regular_years] if regular_years else sessions
                for number in range(1, course.total_semesters + 1):
                    amount = row.get(f"sem_{number}_fee_inr")
                    semester = semester_objects.get((course.name, number))
                    if amount is None or semester is None:
                        continue
                    for session in regular_sessions or [None]:
                        base_year = session.start_year.year if session else int(row.get("syllabus_year") or 2026)
                        fee_rows_to_create.append(FeeStructure(
                            course=course, session=session, semester=semester,
                            title=f"Semester {number} Tuition", amount=Decimal(str(amount)),
                            due_date=semester_due_date(base_year, number), is_active=True,
                            entry_type=FeeStructure.EntryType.REGULAR,
                        ))
                lateral_row = lateral.get(course.name, {})
                if course.lateral_entry_applicable:
                    lateral_years = years_from_duration(lateral_row.get("Duration After Lateral Entry"))
                    lateral_sessions = [session for session in sessions if session.end_year.year - session.start_year.year == lateral_years] if lateral_years else sessions
                    for number in range(3, course.total_semesters + 1):
                        amount = lateral_row.get(f"Semester {number} Fee")
                        semester = semester_objects.get((course.name, number))
                        if amount is None or semester is None:
                            continue
                        for session in lateral_sessions or [None]:
                            base_year = session.start_year.year if session else int(row.get("syllabus_year") or 2026)
                            fee_rows_to_create.append(FeeStructure(
                                course=course, session=session, semester=semester,
                                title=f"Semester {number} Tuition (Lateral Entry)", amount=Decimal(str(amount)),
                                due_date=semester_due_date(base_year, number), is_active=True,
                                entry_type=FeeStructure.EntryType.LATERAL,
                            ))
            FeeStructure.objects.bulk_create(fee_rows_to_create, batch_size=500)
            fee_schedules_created = len(fee_rows_to_create)

            unmatched_students = sum(1 for _, course_name, _, _ in student_assignments if not course_name)
            unmatched_teachers = sum(1 for _, course_name in staff_assignments if not course_name)
            preserved_subject_assignments = sum(bool(subject.staff_id) for subject in subjects_to_create)
            unmatched_subject_assignments = max(0, old_assigned_subject_count - preserved_subject_assignments)

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(courses)} active courses, {len(semester_objects)} semesters, "
            f"{len(subjects_to_create)} subjects, {fee_schedules_created} active fee schedules. "
            f"Preserved {Student.objects.count()} student, {Staff.objects.count()} teacher, and all admin/user accounts; "
            f"mapped {mapped_students} students, {preserved_subject_assignments} teacher-subject assignments "
            f"({unmatched_subject_assignments} previous assignments did not match a workbook subject and were left unassigned). "
            f"Unmatched users remain in the system but need course reassignment: {unmatched_students} students, {unmatched_teachers} teachers."
        ))

