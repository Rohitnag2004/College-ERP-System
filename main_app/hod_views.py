import json
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.urls import reverse
from django.views.generic import UpdateView
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST

from .forms import *
from .models import *
from .portal_views import duration_years, role_required


@role_required("1")
def admin_home(request):
    total_staff = Staff.objects.count()
    total_students = Student.objects.count()
    total_subject = Subject.objects.count()
    total_course = Course.objects.count()
    total_attendance = Attendance.objects.count()

    # Keep dashboard chart payloads bounded; the academic catalogue may contain
    # thousands of subjects, so rendering/querying every row here is wasteful.
    subjects_for_charts = list(
        Subject.objects.values("id", "name", "course_id")
        .annotate(attendance_count=Count("attendance", distinct=True))
        .order_by("-attendance_count", "name")[:12]
    )
    subject_list = [row["name"] for row in subjects_for_charts]
    attendance_list = [row["attendance_count"] for row in subjects_for_charts]
    student_count_list_in_subject = list(
        Student.objects.filter(course_id__in={row["course_id"] for row in subjects_for_charts})
        .values("course_id").annotate(total=Count("pk"))
    )
    students_by_course = {row["course_id"]: row["total"] for row in student_count_list_in_subject}
    student_count_list_in_subject = [students_by_course.get(row["course_id"], 0) for row in subjects_for_charts]

    courses = list(Course.objects.annotate(
        subject_total=Count("subject", distinct=True),
        student_total=Count("student", distinct=True),
    ).order_by("name"))
    course_name_list = [course.name for course in courses]
    subject_count_list = [course.subject_total for course in courses]
    student_count_list_in_course = [course.student_total for course in courses]

    recent_students = list(
        Student.objects.select_related("admin").order_by("-pk")[:12]
    )
    recent_student_ids = [student.pk for student in recent_students]
    attendance_by_student = {
        row["student_id"]: row
        for row in AttendanceReport.objects.filter(student_id__in=recent_student_ids)
        .values("student_id")
        .annotate(
            present=Count("pk", filter=Q(status=True)),
            absent=Count("pk", filter=Q(status=False)),
        )
    }
    leave_by_student = {
        row["student_id"]: row["total"]
        for row in LeaveReportStudent.objects.filter(student_id__in=recent_student_ids, status=1)
        .values("student_id").annotate(total=Count("pk"))
    }
    student_name_list = [student.admin.first_name or student.admin.email for student in recent_students]
    student_attendance_present_list = [attendance_by_student.get(student.pk, {}).get("present", 0) for student in recent_students]
    student_attendance_leave_list = [
        attendance_by_student.get(student.pk, {}).get("absent", 0) + leave_by_student.get(student.pk, 0)
        for student in recent_students
    ]

    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'subject_list_json': json.dumps(subject_list),
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        "student_name_list": student_name_list,
        "student_name_list_json": json.dumps(student_name_list),
        "student_count_list_in_subject": student_count_list_in_subject,
        "student_count_list_in_course": student_count_list_in_course,
        "course_name_list": course_name_list,
        "course_name_list_json": json.dumps(course_name_list),

    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Teacher'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            try:
                with transaction.atomic():
                    user = CustomUser.objects.create_user(
                        email=email, password=password, user_type="2", first_name=first_name,
                        last_name=last_name, profile_pic=request.FILES.get('profile_pic'),
                        gender=gender, address=address)
                    user.staff.course = course
                    user.staff.approval_status = Staff.ApprovalStatus.APPROVED
                    user.staff.approved_at = timezone.now()
                    user.staff.reviewed_by = request.user
                    user.staff.save(update_fields=['course', 'approval_status', 'approved_at', 'reviewed_by'])
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            course = student_form.cleaned_data.get('course')
            session = student_form.cleaned_data.get('session')
            try:
                with transaction.atomic():
                    user = CustomUser.objects.create_user(
                        email=email, password=password, user_type="3", first_name=first_name,
                        last_name=last_name, profile_pic=request.FILES.get('profile_pic'),
                        gender=gender, address=address)
                    user.student.session = session
                    user.student.course = course
                    user.student.semester = student_form.cleaned_data.get('semester')
                    user.student.save(update_fields=['session', 'course', 'semester'])
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_course_template.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                subject = form.save(commit=False)
                subject.save()
                messages.success(request, "Subject saved. Admin changes are treated as final.")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type="2").select_related("staff__course")
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Teachers'
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    students = CustomUser.objects.filter(user_type="3").select_related("student__course")
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'page_title': 'Manage Courses'
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.select_related("course", "staff__admin", "semester").prefetch_related("co_teachers__admin")
    selected_course = request.GET.get("course", "").strip()
    selected_session = request.GET.get("session", "").strip()
    selected_semester = request.GET.get("semester", "").strip()
    selected_subject = request.GET.get("subject", "").strip()
    if selected_course.isdigit():
        subjects = subjects.filter(course_id=int(selected_course))
    else:
        selected_course = ""
    if selected_semester.isdigit():
        subjects = subjects.filter(semester_id=int(selected_semester))
    else:
        selected_semester = ""
    if selected_subject:
        subjects = subjects.filter(name__icontains=selected_subject)
    # Subjects are defined for a course and semester; a session filter scopes
    # the list to courses with students in that cohort without duplicating the
    # same curriculum for every academic batch.
    if selected_session.isdigit():
        enrolled_course_ids = Student.objects.filter(session_id=int(selected_session)).values_list("course_id", flat=True)
        subjects = subjects.filter(course_id__in=enrolled_course_ids)
    else:
        selected_session = ""
    if request.method == "POST" and request.POST.get("action") == "assign_teacher":
        subject = get_object_or_404(Subject, pk=request.POST.get("subject_id"))
        teacher_id = request.POST.get("staff_id", "").strip()
        if teacher_id:
            subject.staff = get_object_or_404(Staff, pk=teacher_id, approval_status=Staff.ApprovalStatus.APPROVED)
        else:
            subject.staff = None
        if "co_teacher_ids" in request.POST:
            co_teacher_ids = request.POST.getlist("co_teacher_ids")
            subject.co_teachers.set(
                Staff.objects.filter(pk__in=co_teacher_ids, approval_status=Staff.ApprovalStatus.APPROVED).exclude(pk=teacher_id or None)
            )
        # An admin assignment is final; no separate curriculum review step.
        subject.save(update_fields=("staff", "updated_at"))
        messages.success(request, f"Teacher assignment saved for {subject.name}.")
        return redirect("manage_subject")
    context = {
        'subjects': subjects.order_by("course__name", "semester__number", "name"),
        'courses': Course.objects.order_by("name"),
        'sessions': Session.objects.order_by("start_year"),
        'semesters': Semester.objects.select_related("course").order_by("course__name", "number"),
        'teachers': Staff.objects.filter(approval_status=Staff.ApprovalStatus.APPROVED).select_related("admin").order_by("admin__first_name", "admin__last_name"),
        'selected_course': selected_course, 'selected_session': selected_session,
        'selected_semester': selected_semester, 'selected_subject': selected_subject,
        'page_title': 'Manage Subjects',
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff.objects.select_related("admin", "course"), id=staff_id)
    form = StaffEditForm(request.POST or None, request.FILES or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = CustomUser.objects.select_for_update().get(pk=staff.admin_id)
                    user.email = form.cleaned_data['email']
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.gender = form.cleaned_data['gender']
                    user.address = form.cleaned_data['address']
                    if form.cleaned_data.get('account_active'):
                        user.is_active = form.cleaned_data['account_active'] == "1"
                    if form.cleaned_data.get('password'):
                        user.set_password(form.cleaned_data['password'])
                    if form.cleaned_data.get('profile_pic'):
                        user.profile_pic = form.cleaned_data['profile_pic']
                    elif form.cleaned_data.get('remove_profile_pic'):
                        user.profile_pic = None
                    user.save()

                    staff.course = form.cleaned_data['course']
                    requested_status = form.cleaned_data.get('approval_status')
                    if requested_status:
                        staff.approval_status = requested_status
                    if staff.approval_status == Staff.ApprovalStatus.APPROVED:
                        if not staff.approved_at:
                            staff.approved_at = timezone.now()
                        staff.reviewed_by = request.user
                    else:
                        staff.approved_at = None
                        if requested_status:
                            staff.reviewed_by = request.user
                    staff.save(update_fields=['course', 'approval_status', 'approved_at', 'reviewed_by'])
                messages.success(request, "Teacher account updated successfully.")
                return redirect('manage_staff')
            except Exception:
                messages.error(request, "Could not update teacher account. Please check the submitted details and try again.")
        else:
            messages.error(request, "Please correct the highlighted teacher details.")
    return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student.objects.select_related("admin", "course", "session"), id=student_id)
    form = StudentEditForm(request.POST or None, request.FILES or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    old_course = student.course
                    student = Student.objects.select_for_update().get(pk=student_id)
                    user = CustomUser.objects.select_for_update().get(pk=student.admin_id)
                    user.email = form.cleaned_data['email']
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.gender = form.cleaned_data['gender']
                    user.address = form.cleaned_data['address']
                    if form.cleaned_data.get('account_active'):
                        user.is_active = form.cleaned_data['account_active'] == "1"
                    if form.cleaned_data.get('password'):
                        user.set_password(form.cleaned_data['password'])
                    if form.cleaned_data.get('profile_pic'):
                        user.profile_pic = form.cleaned_data['profile_pic']
                    elif form.cleaned_data.get('remove_profile_pic'):
                        user.profile_pic = None
                    user.save()

                    student.course = form.cleaned_data['course']
                    student.semester = form.cleaned_data['semester']
                    student.session = form.cleaned_data['session']
                    student.can_edit_profile = form.cleaned_data.get('can_edit_profile', False)
                    student.save(update_fields=['course', 'semester', 'session', 'can_edit_profile'])

                    course = student.course
                    registration = CourseRegistration.objects.select_for_update().filter(
                        student=student, status=CourseRegistration.Status.APPROVED
                    ).first()
                    if registration and course:
                        if registration.course_id != course.pk:
                            old_name = old_course.name if old_course else registration.course.name
                            note = f"Course reassigned by Admin from {old_name} to {course.name} on {timezone.localdate():%Y-%m-%d}."
                            registration.admin_note = "\n".join(part for part in (registration.admin_note, note) if part)
                        registration.course = course
                        registration.session = student.session
                        registration.reviewed_at = timezone.now()
                        registration.reviewed_by = request.user
                        registration.save(update_fields=['course', 'session', 'reviewed_at', 'reviewed_by', 'admin_note'])
                    elif registration:
                        note = f"Course enrollment cleared by Admin on {timezone.localdate():%Y-%m-%d}."
                        registration.status = CourseRegistration.Status.REJECTED
                        registration.reviewed_at = timezone.now()
                        registration.reviewed_by = request.user
                        registration.admin_note = "\n".join(part for part in (registration.admin_note, note) if part)
                        registration.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'admin_note'])
                    elif course:
                        registration = CourseRegistration.objects.select_for_update().filter(
                            student=student,
                            course=course,
                            session=student.session,
                            status=CourseRegistration.Status.PENDING,
                        ).first()
                        if registration:
                            registration.status = CourseRegistration.Status.APPROVED
                            registration.reviewed_at = timezone.now()
                            registration.reviewed_by = request.user
                            registration.admin_note = "\n".join(part for part in (
                                registration.admin_note,
                                "Approved by Admin while updating the student profile.",
                            ) if part)
                            registration.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'admin_note'])
                        else:
                            CourseRegistration.objects.create(
                                student=student,
                                course=course,
                                session=student.session,
                                status=CourseRegistration.Status.APPROVED,
                                reviewed_at=timezone.now(),
                                reviewed_by=request.user,
                                admin_note="Course assigned by Admin while updating the student profile.",
                            )
                    pending_registrations = CourseRegistration.objects.filter(
                        student=student, status=CourseRegistration.Status.PENDING
                    )
                    if course:
                        pending_registrations = pending_registrations.exclude(course=course, session=student.session)
                    if pending_registrations.exists():
                        pending_registrations.update(
                            status=CourseRegistration.Status.REJECTED,
                            reviewed_at=timezone.now(),
                            reviewed_by=request.user,
                            admin_note="Closed by Admin because the student's assigned course was changed or cleared.",
                        )
                messages.success(request, "Student account and course updated successfully.")
                return redirect('manage_student')
            except Exception:
                messages.error(request, "Could not update the student account. Please check the submitted details and try again.")
        else:
            messages.error(request, "Please correct the highlighted student details.")
    return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_course', args=[course_id]))
            except Exception:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            semester = form.cleaned_data.get('semester')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.semester = semester
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_session_template.html", context)


def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)


def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.select_related("student__admin", "student__session").order_by("-created_at")
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.select_related("staff__admin", "staff__course").order_by("-created_at")
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Teacher Feedback Messages'
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.select_related("staff__admin", "staff__course").order_by("-created_at")
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Teachers'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse("False", status=400)


def view_student_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStudent.objects.select_related("student__admin", "student__course").order_by("-created_at")
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse("False", status=400)


def admin_view_attendance(request):
    courses = list(Course.objects.order_by("name"))
    for course in courses:
        course.duration_years = duration_years(course.duration)
    sessions = list(Session.objects.order_by("start_year", "end_year"))
    for session in sessions:
        session.duration_years = session.end_year.year - session.start_year.year
    context = {
        'sessions': sessions,
        'courses': courses,
        'page_title': 'View Attendance'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


@require_GET
def get_admin_attendance_subjects(request):
    if str(getattr(request.user, "user_type", "")) != "1":
        return JsonResponse({"error": "Administrator access is required."}, status=403)
    course_id = request.GET.get("course")
    session_id = request.GET.get("session")
    try:
        course = get_object_or_404(Course, pk=course_id)
        session = get_object_or_404(Session, pk=session_id)
        if session.end_year.year - session.start_year.year != duration_years(course.duration):
            return JsonResponse({"error": "Choose an academic session matching this course duration."}, status=400)
        subjects = Subject.objects.filter(course=course, semester__isnull=False).values(
            "id", "code", "name", "semester_id", "semester__name"
        ).order_by("semester__number", "name", "code")
        return JsonResponse([
            {
                "id": row["id"],
                "code": row["code"],
                "name": row["name"],
                "semester": row["semester_id"],
                "label": f"{row['code'] + ' — ' if row['code'] else ''}{row['name']}",
            }
            for row in subjects
        ], safe=False)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Choose a valid course and session."}, status=400)


def get_admin_attendance(request):
    if str(getattr(request.user, "user_type", "")) != "1":
        return JsonResponse({"error": "Administrator access is required."}, status=403)
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session_id=session_id, subject_id=subject_id)
        enrolled_students = Student.objects.filter(
            course=attendance.subject.course, semester=attendance.semester,
            session=attendance.session,
        ).select_related("admin").order_by("admin__first_name", "admin__last_name")
        reports = {
            row.student_id: row for row in AttendanceReport.objects.filter(attendance=attendance)
        }
        json_data = []
        for student in enrolled_students:
            report = reports.get(student.pk)
            data = {
                "id": student.pk,
                "report_id": report.pk if report else None,
                "status": report.attendance_status if report else "removed",
                "name": student.admin.get_full_name() or student.admin.email,
            }
            json_data.append(data)
        return JsonResponse(json_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": "Unable to load attendance for the selected class."}, status=400)


@require_POST
def admin_save_attendance(request):
    if str(getattr(request.user, "user_type", "")) != "1":
        return JsonResponse({"error": "Administrator access is required."}, status=403)
    try:
        attendance = get_object_or_404(
            Attendance.objects.select_related("subject", "semester", "session"),
            pk=request.POST.get("attendance_id"),
        )
        items = json.loads(request.POST.get("student_ids", "[]"))
        if not isinstance(items, list):
            raise ValueError
        student_ids = [int(item["id"]) for item in items]
        if len(student_ids) != len(set(student_ids)):
            return JsonResponse({"error": "Duplicate students were submitted."}, status=400)
        enrolled = {
            student.pk: student for student in Student.objects.filter(
                pk__in=student_ids, course=attendance.subject.course,
                semester=attendance.semester, session=attendance.session,
            )
        }
        if len(enrolled) != len(student_ids):
            return JsonResponse({"error": "A student is outside this attendance class."}, status=400)
        valid = set(AttendanceReport.Status.values) | {"removed"}
        statuses = {int(item["id"]): item.get("status") for item in items}
        if any(value not in valid for value in statuses.values()):
            return JsonResponse({"error": "Choose a valid attendance status."}, status=400)
        with transaction.atomic():
            existing = {
                report.student_id: report for report in AttendanceReport.objects.select_for_update().filter(
                    attendance=attendance, student_id__in=student_ids
                )
            }
            changed, created = [], []
            for student_id, status in statuses.items():
                if status == "removed":
                    if student_id in existing:
                        existing[student_id].delete()
                    continue
                is_present = status in {"present", "late"}
                report = existing.get(student_id)
                if report:
                    report.attendance_status = status
                    report.status = is_present
                    report.updated_at = timezone.now()
                    changed.append(report)
                else:
                    created.append(AttendanceReport(
                        attendance=attendance, student=enrolled[student_id],
                        attendance_status=status, status=is_present,
                    ))
            if changed:
                AttendanceReport.objects.bulk_update(changed, ("attendance_status", "status", "updated_at"))
            if created:
                AttendanceReport.objects.bulk_create(created)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "The attendance update is invalid."}, status=400)
    return JsonResponse({"ok": True})


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    custom_user.profile_pic = passport
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Teachers",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type="3")
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)


def send_student_notification(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
    id = request.POST.get('id')
    message = request.POST.get('message', '').strip()
    student = get_object_or_404(Student, admin_id=id)
    if not message:
        return HttpResponse("A message is required", status=400)
    NotificationStudent.objects.create(student=student, message=message)
    return HttpResponse("True")


def send_staff_notification(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
    id = request.POST.get('id')
    message = request.POST.get('message', '').strip()
    staff = get_object_or_404(Staff, admin_id=id)
    if not message:
        return HttpResponse("A message is required", status=400)
    NotificationStaff.objects.create(staff=staff, message=message)
    return HttpResponse("True")


def delete_staff(request, staff_id):
    staff = get_object_or_404(CustomUser, staff__id=staff_id)
    staff.delete()
    messages.success(request, "Teacher deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again")
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))
