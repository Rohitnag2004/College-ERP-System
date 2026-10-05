import json

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_POST
from .forms import *
from .models import *
from . import forms, models
from datetime import date
from django.utils import timezone
from .portal_views import duration_years, role_required


def _subjects_visible_to(request):
    subjects = Subject.objects.select_related("course", "staff")
    if request.user.user_type == "2":
        return subjects.filter(Q(staff__admin=request.user) | Q(co_teachers__admin=request.user)).distinct()
    if request.user.user_type == "1":
        return subjects
    return subjects.none()

@role_required("2")
def staff_home(request):
    staff = get_object_or_404(Staff.objects.select_related("admin", "course"), admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = list(
        Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff)).distinct()
        .annotate(attendance_count=Count("attendance"))
        .order_by("semester__number", "name")
    )
    total_subject = len(subjects)
    subject_list = [subject.name for subject in subjects]
    attendance_list = [subject.attendance_count for subject in subjects]
    total_attendance = sum(attendance_list)
    context = {
        'page_title': 'Teacher Portal - ' + str(staff.admin.first_name) + ' ' + str(staff.admin.last_name[:1]) + ' (' + str(staff.course or 'Unassigned') + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, "staff_template/erpnext_staff_home.html", context)


@role_required("2")
def staff_work_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user, approval_status=Staff.ApprovalStatus.APPROVED)
    today = timezone.localdate()
    record = TeacherAttendance.objects.filter(staff=staff, work_date=today).first()
    history = TeacherAttendance.objects.filter(staff=staff)[:30]
    return render(request, "staff_template/work_attendance.html", {
        "page_title": "My Work Attendance", "record": record, "history": history,
    })


@role_required("2")
@require_POST
def mark_work_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user, approval_status=Staff.ApprovalStatus.APPROVED)
    now = timezone.now()
    action = request.POST.get("action")
    if action == "check_in":
        record, _ = TeacherAttendance.objects.get_or_create(staff=staff, work_date=timezone.localdate())
        if record.checked_in_at:
            messages.info(request, "Your check-in is already recorded for today.")
        else:
            record.checked_in_at = now
            record.note = request.POST.get("note", "").strip()[:240]
            record.save(update_fields=("checked_in_at", "note", "updated_at"))
            messages.success(request, "Check-in recorded with the server time.")
    elif action == "check_out":
        record = TeacherAttendance.objects.filter(staff=staff, work_date=timezone.localdate()).first()
        if not record:
            messages.error(request, "Check in before checking out.")
            return redirect("staff_work_attendance")
        if not record.checked_in_at:
            messages.error(request, "Check in before checking out.")
        elif record.checked_out_at:
            messages.info(request, "Your check-out is already recorded for today.")
        else:
            record.checked_out_at = now
            record.save(update_fields=("checked_out_at", "updated_at"))
            messages.success(request, "Check-out recorded with the server time.")
    else:
        messages.error(request, "Choose a valid attendance action.")
    return redirect("staff_work_attendance")


@role_required("2")
def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = list(Subject.objects.filter(
        Q(staff=staff) | Q(co_teachers=staff), semester__isnull=False,
    ).select_related("course", "semester").distinct().order_by("course__name", "semester__number", "name"))
    course_ids = {subject.course_id for subject in subjects}
    semester_ids = {subject.semester_id for subject in subjects}
    course_years = {duration_years(subject.course.duration) for subject in subjects}
    course_years.discard(None)
    sessions = [
        session for session in Session.objects.order_by("start_year", "end_year")
        if session.end_year.year - session.start_year.year in course_years
    ]
    context = {
        'subjects': subjects,
        'courses': Course.objects.filter(pk__in=course_ids).order_by("name"),
        'semesters': Semester.objects.filter(pk__in=semester_ids).select_related("course").order_by("course__name", "number"),
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@role_required("2")
@require_POST
def get_students(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subject_id = request.POST.get('subject')
    course_id = request.POST.get('course')
    semester_id = request.POST.get('semester')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(
            Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff), semester__isnull=False).distinct(),
            id=subject_id, course_id=course_id, semester_id=semester_id,
        )
        session = get_object_or_404(Session, id=session_id)
        if session.end_year.year - session.start_year.year != duration_years(subject.course.duration):
            return JsonResponse({"error": "Choose a session matching this course duration."}, status=400)
        students = Student.objects.filter(
            course=subject.course, semester=subject.semester, session=session,
        ).select_related("admin").order_by("admin__first_name", "admin__last_name")
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.get_full_name() or student.admin.email
                    }
            student_data.append(data)
        return JsonResponse(student_data, safe=False)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Choose a valid subject and session."}, status=400)


@role_required("2")
@require_POST
def save_attendance(request):
    try:
        students_data = json.loads(request.POST.get("student_ids", "[]"))
        attendance_date = parse_date(request.POST.get("date", ""))
        staff = get_object_or_404(Staff, admin=request.user)
        subject = get_object_or_404(
            Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff), semester__isnull=False).distinct(),
            pk=request.POST.get("subject"),
            course_id=request.POST.get("course"),
            semester_id=request.POST.get("semester"),
        )
        session = get_object_or_404(Session, pk=request.POST.get("session"))
        if session.end_year.year - session.start_year.year != duration_years(subject.course.duration):
            return JsonResponse({"error": "Choose a session matching this course duration."}, status=400)
        if not attendance_date or not isinstance(students_data, list) or not students_data:
            return JsonResponse({"error": "Provide a date and at least one student."}, status=400)
        student_ids = [int(item["id"]) for item in students_data]
        if len(student_ids) != len(set(student_ids)):
            return JsonResponse({"error": "The attendance list contains duplicate students."}, status=400)
        students = list(Student.objects.filter(
            pk__in=student_ids, course=subject.course, semester=subject.semester, session=session
        ).select_related("admin"))
        if len(students) != len(student_ids):
            return JsonResponse({"error": "One or more students do not belong to this subject and session."}, status=403)
        allowed = set(AttendanceReport.Status.values)
        statuses = {}
        for item in students_data:
            raw = item.get("status")
            if isinstance(raw, str):
                value = raw
            elif raw in (True, 1, "1"):
                value = "present"
            elif raw in (False, 0, "0", None):
                value = "absent"
            else:
                return JsonResponse({"error": "Choose a valid attendance status."}, status=400)
            if value not in allowed:
                return JsonResponse({"error": "Choose a valid attendance status."}, status=400)
            statuses[int(item["id"])] = value
        starts_at = parse_time(request.POST.get("starts_at", ""))
        ends_at = parse_time(request.POST.get("ends_at", ""))
        if starts_at and ends_at and ends_at <= starts_at:
            return JsonResponse({"error": "Class end time must be after the start time."}, status=400)
        with transaction.atomic():
            attendance = Attendance.objects.create(
                session=session, subject=subject, date=attendance_date,
                semester=subject.semester, class_topic=request.POST.get("class_topic", "").strip()[:180],
                starts_at=starts_at, ends_at=ends_at, created_by=request.user,
            )
            AttendanceReport.objects.bulk_create([
                AttendanceReport(
                    student=student, attendance=attendance,
                    attendance_status=statuses[student.pk],
                    status=statuses[student.pk] in ("present", "late"),
                )
                for student in students
            ])
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "The attendance submission is invalid."}, status=400)
    return HttpResponse("OK")


@role_required("2")
def staff_update_attendance(request):
    # Keep bookmarked links working while attendance management lives in the
    # single Take Attendance workflow.
    return redirect("staff_take_attendance")


@role_required("2", "1")
@require_POST
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        attendance = get_object_or_404(
            Attendance.objects.filter(subject__in=_subjects_visible_to(request)),
            id=attendance_date_id,
        )
        attendance_data = AttendanceReport.objects.filter(attendance=attendance).select_related("student__admin")
        student_data = []
        for attendance_report in attendance_data:
            data = {"id": attendance_report.student.admin.id,
                    "name": attendance_report.student.admin.get_full_name() or attendance_report.student.admin.email,
                    "status": attendance_report.status,
                    "attendance_status": attendance_report.attendance_status}
            student_data.append(data)
        return JsonResponse(student_data, safe=False)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Choose a valid attendance record."}, status=400)


@role_required("2")
@require_POST
def update_attendance(request):
    try:
        students_data = json.loads(request.POST.get("student_ids", "[]"))
        attendance = get_object_or_404(
            Attendance.objects.filter(subject__in=_subjects_visible_to(request)),
            pk=request.POST.get("date"),
        )
        if not isinstance(students_data, list):
            return JsonResponse({"error": "The attendance update is invalid."}, status=400)
        if not students_data:
            return HttpResponse("OK")
        admin_ids = [int(item["id"]) for item in students_data]
        if len(admin_ids) != len(set(admin_ids)):
            return JsonResponse({"error": "The attendance list contains duplicate students."}, status=400)
        reports = list(AttendanceReport.objects.filter(
            attendance=attendance,
            student__admin_id__in=admin_ids,
            student__course=attendance.subject.course,
            student__semester=attendance.semester,
            student__session=attendance.session,
        ).select_related("student"))
        reports_by_admin_id = {report.student.admin_id: report for report in reports}
        if len(reports_by_admin_id) != len(admin_ids):
            return JsonResponse({"error": "One or more students do not belong to this attendance record."}, status=403)

        changed_at = timezone.now()
        for item in students_data:
            raw = item.get("status")
            if isinstance(raw, str) and raw in AttendanceReport.Status.values:
                status = raw
            elif raw in (True, 1, "1"):
                status = "present"
            elif raw in (False, 0, "0", None):
                status = "absent"
            else:
                return JsonResponse({"error": "Choose a valid attendance status."}, status=400)
            report = reports_by_admin_id[int(item["id"])]
            report.attendance_status = status
            report.status = status in ("present", "late")
            report.updated_at = changed_at
        with transaction.atomic():
            AttendanceReport.objects.bulk_update(reports, ["status", "attendance_status", "updated_at"])
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "The attendance update is invalid."}, status=400)
    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    if request.method == 'POST':
        messages.error(request, "Teacher profile changes are managed by the college administrator.")
        return redirect("staff_view_profile")
    return render(request, "staff_template/staff_view_profile.html", {
        'staff': staff,
        'page_title': 'Teacher Profile',
    })


def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff)).distinct()
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = float(request.POST.get('test', ''))
            exam = float(request.POST.get('exam', ''))
            subject = get_object_or_404(_subjects_visible_to(request), id=subject_id)
            student = get_object_or_404(Student, id=student_id, course=subject.course)
            if not (0 <= test <= 40 and 0 <= exam <= 60):
                messages.error(request, "Test scores must be 0–40 and exam scores 0–60.")
            else:
                result, created = StudentResult.objects.update_or_create(
                    student=student,
                    subject=subject,
                    defaults={"test": test, "exam": exam},
                )
                messages.success(request, "Scores saved." if created else "Scores updated.")
        except (TypeError, ValueError):
            messages.error(request, "Choose a valid student and subject and enter numeric scores.")
    return render(request, "staff_template/staff_add_result.html", context)


@require_POST
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        subject = get_object_or_404(_subjects_visible_to(request), id=subject_id)
        student = get_object_or_404(Student, id=student_id, course=subject.course)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except (StudentResult.DoesNotExist, TypeError, ValueError):
        return HttpResponse('False')

#library
def add_book(request):
    if request.method == "POST":
        name = request.POST['name']
        author = request.POST['author']
        isbn = request.POST['isbn']
        category = request.POST['category']


        books = Book.objects.create(name=name, author=author, isbn=isbn, category=category )
        books.save()
        alert = True
        return render(request, "staff_template/add_book.html", {'alert':alert})
    context = {
        'page_title': "Add Book"
    }
    return render(request, "staff_template/add_book.html",context)

#issue book


def issue_book(request):
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            models.IssuedBook.objects.create(
                student_id=str(form.cleaned_data["name2"].pk),
                isbn=str(form.cleaned_data["isbn2"].isbn),
            )
            messages.success(request, "Book issued successfully.")
            return redirect("issue_book")
    else:
        form = forms.IssueBookForm()
    return render(request, "staff_template/issue_book.html", {"form": form, "page_title": "Issue Book"})

def view_issued_book(request):
    records = IssuedBook.objects.order_by("-issued_date", "-pk")
    record_page = Paginator(records, 50).get_page(request.GET.get("page"))
    current_records = list(record_page.object_list)
    isbn_values = {record.isbn for record in current_records}
    book_by_isbn = {str(book.isbn): book for book in Book.objects.filter(isbn__in=isbn_values)}
    student_ids = set()
    for record in current_records:
        try:
            student_ids.add(int(record.student_id))
        except (TypeError, ValueError):
            continue
    student_by_id = {
        str(student.pk): student
        for student in Student.objects.filter(pk__in=student_ids).select_related("admin", "course")
    }
    today = timezone.localdate()
    rows = []
    for record in current_records:
        rows.append({
            "record": record,
            "book": book_by_isbn.get(record.isbn),
            "student": student_by_id.get(record.student_id),
            "fine": max((today - record.expiry_date).days, 0) * 5,
        })
    return render(request, "staff_template/view_issued_book.html", {
        "page_title": "Issued Books", "records": rows, "record_page": record_page,
    })
