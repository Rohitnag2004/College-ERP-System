import json
import math
from datetime import datetime

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from .forms import *
from .models import *
from .portal_views import role_required


def enrolled_course_id(student):
    return student.course_id or CourseRegistration.objects.filter(
        student=student, status=CourseRegistration.Status.APPROVED
    ).values_list("course_id", flat=True).first()


def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    course_id = enrolled_course_id(student)
    subjects = Subject.objects.filter(course_id=course_id).select_related("semester").annotate(
        present_count=Count(
            "attendance__attendancereport",
            filter=Q(attendance__attendancereport__student_id=student.pk, attendance__attendancereport__status=True),
            distinct=True,
        ),
        absent_count=Count(
            "attendance__attendancereport",
            filter=Q(attendance__attendancereport__student_id=student.pk, attendance__attendancereport__status=False),
            distinct=True,
        ),
    ).order_by("semester__number", "name") if course_id else Subject.objects.none()
    subjects = list(subjects)
    total_subject = len(subjects)
    attendance_totals = AttendanceReport.objects.filter(
        student=student, attendance__subject__course_id=course_id
    ).aggregate(total=Count("pk"), present=Count("pk", filter=Q(status=True))) if course_id else {"total": 0, "present": 0}
    total_attendance = attendance_totals["total"]
    total_present = attendance_totals["present"]
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present/total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    subject_name = [subject.name for subject in subjects]
    data_present = [subject.present_count for subject in subjects]
    data_absent = [subject.absent_count for subject in subjects]
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'

    }
    return render(request, 'student_template/erpnext_student_home.html', context)


@role_required("3")
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    course_id = enrolled_course_id(student)
    if request.method != 'POST':
        context = {
            'subjects': Subject.objects.filter(course_id=course_id).select_related('semester') if course_id else Subject.objects.none(),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id, course_id=course_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            if start_date > end_date:
                return HttpResponse("[]", status=400)
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            attendance_reports = attendance_reports.select_related(
                "attendance__subject", "attendance__semester",
            )
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status,
                    "attendance_status": report.attendance_status,
                    "subject": report.attendance.subject.name,
                    "semester": report.attendance.semester.name if report.attendance.semester_id else "",
                    "topic": report.attendance.class_topic,
                    "starts_at": report.attendance.starts_at.strftime("%H:%M") if report.attendance.starts_at else "",
                    "ends_at": report.attendance.ends_at.strftime("%H:%M") if report.attendance.ends_at else "",
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except (TypeError, ValueError):
            return HttpResponse("[]", status=400)


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentSelfProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    ) if student.can_edit_profile else None
    context = {
        'form': form,
        'student': student,
        'page_title': 'View/Edit Profile',
    }
    if request.method == 'POST' and not student.can_edit_profile:
        messages.error(request, "Profile editing is currently disabled by the college administrator.")
        return redirect('student_view_profile')
    if request.method == 'POST' and form:
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Your permitted profile details were updated.")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Please correct the highlighted profile details.")
        except Exception:
            messages.error(request, "Could not update the profile. Please try again.")

    return render(request, "student_template/student_view_profile.html", context)


def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    course_id = enrolled_course_id(student)
    results = StudentResult.objects.filter(student=student, subject__course_id=course_id).select_related("subject", "subject__semester") if course_id else StudentResult.objects.none()
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)


#library

def view_books(request):
    books = Book.objects.all()
    context = {
        'books': books,
        'page_title': "Library"
    }
    return render(request, "student_template/view_books.html", context)

