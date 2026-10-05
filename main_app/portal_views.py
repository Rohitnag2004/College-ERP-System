"""Course registration, fees, and notice board workflows."""

from functools import wraps
from datetime import date
import secrets
import mimetypes
import os
import re
from io import BytesIO
from xml.sax.saxutils import escape
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_POST
from .forms import AdminAccountForm, BookForm, CollegeResourceForm, FeeStructureForm, NoticeForm, StudentGradeCardForm
from .models import Admin, Book, CollegeResource, Course, CourseRegistration, CustomUser, FeePayment, FeeStructure, Notice, PortalAccessSettings, SalaryPayment, Session, Staff, Student, StudentGradeCard, TeacherAttendance, TeacherPayrollProfile, Semester, Subject


def duration_years(value):
    match = re.search(r"(\d+)", str(value or ""))
    return int(match.group(1)) if match else None


def semester_fee_due_date(session, semester):
    """Odd semesters are due by Aug 31; even semesters are due by Jan 31."""
    number = semester.number
    if number % 2:
        year = session.start_year.year + ((number - 1) // 2)
        return date(year, 8, 31)
    year = session.start_year.year + (number // 2)
    return date(year, 1, 31)


def role_required(*allowed_roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            role = str(request.user.user_type)
            if role not in allowed_roles:
                destinations = {"1": "admin_home", "2": "staff_home", "3": "student_home"}
                messages.error(request, "You do not have permission to view that page.")
                return redirect(destinations.get(role, "login_page"))
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


PORTAL_ACCESS_CACHE_KEY = "portal_access_settings_v1"


def portal_access_state():
    state = cache.get(PORTAL_ACCESS_CACHE_KEY)
    if state is None:
        settings_row = PortalAccessSettings.objects.filter(pk=1).values(
            "student_portal_enabled", "teacher_portal_enabled"
        ).first()
        state = settings_row or {"student_portal_enabled": True, "teacher_portal_enabled": True}
        cache.set(PORTAL_ACCESS_CACHE_KEY, state, timeout=5)
    return state


@role_required("1")
def admin_portal_availability(request):
    settings_row, _ = PortalAccessSettings.objects.get_or_create(pk=1)
    if request.method == "POST":
        settings_row.student_portal_enabled = request.POST.get("student_portal_enabled") == "on"
        settings_row.teacher_portal_enabled = request.POST.get("teacher_portal_enabled") == "on"
        settings_row.updated_by = request.user
        settings_row.save(update_fields=("student_portal_enabled", "teacher_portal_enabled", "updated_by", "updated_at"))
        cache.delete(PORTAL_ACCESS_CACHE_KEY)
        messages.success(request, "Portal availability has been updated.")
        return redirect("admin_portal_availability")
    return render(request, "hod_template/portal_availability.html", {
        "page_title": "Portal Availability",
        "settings_row": settings_row,
    })


def portal_maintenance(request):
    if not request.user.is_authenticated:
        return redirect("login_page")
    state = portal_access_state()
    role = str(request.user.user_type)
    disabled = (role == "2" and not state["teacher_portal_enabled"]) or (role == "3" and not state["student_portal_enabled"])
    if not disabled:
        destination = {"1": "admin_home", "2": "staff_home", "3": "student_home"}.get(role, "login_page")
        return redirect(destination)
    role_label = "Teacher" if role == "2" else "Student"
    return render(request, "main_app/portal_maintenance.html", {"role_label": role_label}, status=503)


@role_required("3")
def student_course_registration(request):
    student = request.user.student
    registrations = CourseRegistration.objects.filter(student=student).select_related("course", "session")
    approved_course_id = registrations.filter(status=CourseRegistration.Status.APPROVED).values_list("course_id", flat=True).first()
    enrolled_course_id = student.course_id or approved_course_id
    has_approved_course = bool(enrolled_course_id)
    courses = Course.objects.filter(is_active=True)
    if enrolled_course_id:
        courses = Course.objects.filter(pk=enrolled_course_id)
    if request.method == "POST":
        course = get_object_or_404(Course, pk=request.POST.get("course_id"), is_active=True)
        session_id = request.POST.get("session_id") or ""
        session = get_object_or_404(Session, pk=session_id) if session_id else None
        if not session and student.session_id:
            current_session = student.session
            if current_session.end_year.year - current_session.start_year.year == duration_years(course.duration):
                session = current_session
        if not session or session.end_year.year - session.start_year.year != duration_years(course.duration):
            messages.error(request, "Choose an academic session that matches the selected course duration.")
            return redirect("student_course_registration")
        admission_type = request.POST.get("admission_type", Student.EntryType.REGULAR)
        if admission_type not in Student.EntryType.values or (admission_type == Student.EntryType.LATERAL and not course.lateral_entry_applicable):
            admission_type = Student.EntryType.REGULAR
        try:
            with transaction.atomic():
                student = type(student).objects.select_for_update().get(pk=student.pk)
                registrations = CourseRegistration.objects.filter(student=student)
                existing = registrations.filter(status="approved").first()
                if existing:
                    if existing.course_id == course.pk:
                        messages.info(request, "You are already enrolled in your one permitted course.")
                    else:
                        messages.error(request, "You are already enrolled in a course. Contact the administration if you need to change it.")
                    return redirect("student_course_registration")
                if student.course_id and student.course_id != course.pk:
                    messages.error(request, "Your profile already has a course assigned. Contact the administration if you need to change it.")
                    return redirect("student_course_registration")
                if registrations.filter(course=course, session=session, status="pending").exists():
                    messages.info(request, "A registration for this course is already awaiting review.")
                    return redirect("student_course_registration")
                CourseRegistration.objects.create(
                    student=student, course=course, session=session,
                    status=CourseRegistration.Status.APPROVED,
                    reviewed_at=timezone.now(),
                    admin_note="Automatically approved when submitted by the student.",
                )
                student.course = course
                student.admission_type = admission_type
                if not student.semester or student.semester.course_id != course.pk:
                    first_semester_number = course.lateral_entry_semester if admission_type == Student.EntryType.LATERAL else 1
                    student.semester = Semester.objects.filter(course=course, is_active=True, number=first_semester_number).first()
                if session:
                    student.session = session
                student.save(update_fields=("course", "semester", "session", "admission_type"))
            messages.success(request, "Your course registration is approved. The selected course is now on your student profile.")
        except IntegrityError:
            messages.info(request, "A registration for this course and session is already on your account.")
        return redirect("student_course_registration")
    courses = list(courses.prefetch_related("semesters__subjects").order_by("name"))
    for course in courses:
        course.duration_years = duration_years(course.duration)
        # The selected session identifies the full program cohort, even when
        # a learner starts from the lateral-entry semester.
        course.lateral_duration_years = course.duration_years if course.lateral_entry_applicable else None
    sessions = list(Session.objects.order_by("-start_year"))
    for session in sessions:
        session.duration_years = session.end_year.year - session.start_year.year
    return render(request, "student_template/course_registration.html", {
        "page_title": "Course Registration", "courses": courses,
        "registrations": registrations, "student": student,
        "has_approved_course": has_approved_course, "enrolled_course_id": enrolled_course_id,
        "sessions": sessions,
    })


@role_required("1")
def admin_course_registrations(request):
    status = request.GET.get("status", "pending")
    search_query = request.GET.get("q", "").strip()
    registrations = CourseRegistration.objects.select_related("student__admin", "course", "session", "reviewed_by")
    if status in CourseRegistration.Status.values:
        registrations = registrations.filter(status=status)
    else:
        status = "all"
    if search_query:
        registrations = registrations.filter(
            Q(student__admin__first_name__icontains=search_query) |
            Q(student__admin__last_name__icontains=search_query) |
            Q(student__admin__email__icontains=search_query) |
            Q(course__name__icontains=search_query)
        )
    registration_page = Paginator(registrations, 50).get_page(request.GET.get("page"))
    return render(request, "hod_template/course_registrations.html", {
        "page_title": "Course Registration Requests", "registrations": registration_page,
        "status_filter": status, "search_query": search_query,
    })


@role_required("1")
def manage_teacher_approvals(request):
    if request.method == "POST":
        staff = get_object_or_404(Staff.objects.select_related("admin"), pk=request.POST.get("staff_id"))
        decision = request.POST.get("decision")
        if decision not in {Staff.ApprovalStatus.APPROVED, Staff.ApprovalStatus.REJECTED}:
            messages.error(request, "Choose Approve or Reject for this Teacher account.")
        else:
            staff.approval_status = decision
            staff.reviewed_by = request.user
            staff.approved_at = timezone.now() if decision == Staff.ApprovalStatus.APPROVED else None
            staff.save(update_fields=("approval_status", "reviewed_by", "approved_at"))
            label = "approved" if decision == Staff.ApprovalStatus.APPROVED else "rejected"
            messages.success(request, f"Teacher account {label}.")
        return redirect("manage_teacher_approvals")

    status = request.GET.get("status", "pending")
    teachers = Staff.objects.select_related("admin", "course", "reviewed_by")
    if status in Staff.ApprovalStatus.values:
        teachers = teachers.filter(approval_status=status)
    else:
        status = "all"
    return render(request, "hod_template/teacher_approvals.html", {
        "page_title": "Teacher Account Approval", "teachers": teachers, "status_filter": status,
    })


@role_required("1")
def manage_admin_accounts(request):
    form = AdminAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                CustomUser.objects.create_user(
                    email=data["email"], password=data["password"], user_type="1",
                    first_name=data["first_name"].strip(), last_name=data["last_name"].strip(),
                )
        except IntegrityError:
            form.add_error("email", "An account with this email address already exists.")
        else:
            messages.success(request, "Admin account created. Share its sign-in details securely with the new administrator.")
            return redirect("manage_admin_accounts")
    admins = Admin.objects.select_related("admin").order_by("admin__email")
    return render(request, "hod_template/admin_accounts.html", {
        "page_title": "Admin Accounts", "form": form, "admins": admins,
    })


@role_required("1")
@require_POST
def review_course_registration(request, registration_id):
    decision = request.POST.get("decision")
    if decision not in {"approved", "rejected"}:
        messages.error(request, "Choose Approve or Reject to review a registration.")
        return redirect("admin_course_registrations")
    with transaction.atomic():
        registration = get_object_or_404(
            CourseRegistration.objects.select_for_update().select_related("student", "course", "session"), pk=registration_id
        )
        if registration.status != "pending":
            messages.warning(request, "This registration has already been reviewed.")
            return redirect("admin_course_registrations")
        if decision == "approved" and CourseRegistration.objects.filter(
            student=registration.student, status=CourseRegistration.Status.APPROVED
        ).exists():
            messages.error(request, "This student already has an approved course. Resolve the existing enrollment before approving another.")
            return redirect("admin_course_registrations")
        if decision == "approved" and registration.student.course_id and registration.student.course_id != registration.course_id:
            messages.error(request, "This student profile already has a different course assigned. Update the profile before approving this registration.")
            return redirect("admin_course_registrations")
        try:
            with transaction.atomic():
                registration.status = decision
                registration.reviewed_by = request.user
                registration.reviewed_at = timezone.now()
                registration.admin_note = request.POST.get("admin_note", "").strip()
                registration.save(update_fields=("status", "reviewed_by", "reviewed_at", "admin_note"))
                if decision == "approved":
                    registration.student.course = registration.course
                    if not registration.student.semester or registration.student.semester.course_id != registration.course_id:
                        registration.student.semester = Semester.objects.filter(
                            course=registration.course, is_active=True,
                        ).order_by("number").first()
                    registration.student.session = registration.session
                    registration.student.save(update_fields=("course", "semester", "session"))
        except IntegrityError:
            messages.error(request, "This student already has an approved course. Resolve the existing enrollment before approving another.")
            return redirect("admin_course_registrations")
    messages.success(request, f"Registration {registration.get_status_display().lower()}.")
    return redirect("admin_course_registrations")


@role_required("3")
def student_fees(request):
    student = request.user.student
    payments = FeePayment.objects.filter(student=student).select_related("fee", "fee__course", "fee__session", "fee__semester")
    if student.course_id:
        fee_rows = FeeStructure.objects.filter(course=student.course, entry_type=student.admission_type)
        if student.session_id:
            fee_rows = fee_rows.filter(Q(session=student.session) | Q(session__isnull=True))
        else:
            fee_rows = fee_rows.filter(session__isnull=True)
        fee_ids = list(fee_rows.values_list("pk", flat=True))
        existing_fee_ids = set(FeePayment.objects.filter(student=student, fee_id__in=fee_ids).values_list("fee_id", flat=True))
        FeePayment.objects.bulk_create(
            [FeePayment(student=student, fee_id=fee_id) for fee_id in fee_ids if fee_id not in existing_fee_ids],
            ignore_conflicts=True,
        )
        payments = payments.filter(fee_id__in=fee_ids).order_by("fee__due_date", "fee__semester__number")
    payments = list(payments)
    active_payments = [item for item in payments if item.fee.is_active]
    paid_total = sum((item.fee.amount for item in active_payments if item.status == FeePayment.Status.PAID), Decimal("0.00"))
    total_fees = sum((item.fee.amount for item in active_payments), Decimal("0.00"))
    program_tuition_total = (
        student.course.lateral_entry_total_fee
        if student.course_id and student.admission_type == Student.EntryType.LATERAL and student.course.lateral_entry_total_fee is not None
        else (student.course.total_fee if student.course_id else None)
    )
    return render(request, "student_template/fees.html", {
        "page_title": "My Fees", "payments": payments, "student": student,
        "total_fees": total_fees, "paid_total": paid_total, "due_total": total_fees - paid_total,
        "program_tuition_total": program_tuition_total,
    })


@role_required("3")
def demo_fee_checkout(request, payment_id):
    payment = get_object_or_404(
        FeePayment.objects.select_related("fee__course", "fee__semester"),
        pk=payment_id, student=request.user.student,
    )
    if request.method == "POST":
        if not payment.fee.is_active:
            messages.error(request, "This fee is awaiting confirmation by the administration.")
            return redirect("student_fees")
        if payment.status == FeePayment.Status.PAID:
            messages.info(request, "This fee has already been approved.")
            return redirect("student_fees")
        if payment.status == FeePayment.Status.PENDING:
            messages.info(request, "This demo payment is already awaiting Admin approval.")
            return redirect("student_fees")
        if request.POST.get("confirm_demo") != "yes":
            messages.error(request, "Confirm the demo payment to submit it for Admin approval.")
            return redirect("demo_fee_checkout", payment_id=payment.pk)
        method = request.POST.get("demo_method", "UPI")
        if method not in {"UPI", "CARD", "NETBANKING"}:
            messages.error(request, "Choose one of the available demo payment methods.")
            return redirect("demo_fee_checkout", payment_id=payment.pk)
        payment.status = FeePayment.Status.PENDING
        payment.payment_reference = f"DEMO-{method}-{secrets.token_hex(5).upper()}"
        payment.submitted_at = timezone.now()
        payment.reviewed_at = None
        payment.reviewed_by = None
        payment.admin_note = ""
        payment.save(update_fields=("status", "payment_reference", "submitted_at", "reviewed_at", "reviewed_by", "admin_note"))
        messages.success(request, "Demo payment submitted. No money was charged; wait for Admin approval.")
        return redirect("student_fees")
    return render(request, "student_template/demo_checkout.html", {
        "page_title": "Demo Payment", "payment": payment,
    })


@role_required("1")
def admin_fees(request):
    search_query = (request.GET.get("q") or request.POST.get("q", "")).strip()
    selected_course = (request.GET.get("course_id") or request.POST.get("course_id", "")).strip()
    selected_session = (request.GET.get("session_id") or request.POST.get("session_id", "")).strip()
    selected_entry_type = (request.GET.get("entry_type") or request.POST.get("entry_type", "")).strip()
    selected_semester = (request.GET.get("semester_id") or request.POST.get("semester_id", "")).strip()
    selected_title = (request.GET.get("title") or request.POST.get("title", "")).strip()
    selected_min_amount = (request.GET.get("min_amount") or request.POST.get("min_amount", "")).strip()
    selected_max_amount = (request.GET.get("max_amount") or request.POST.get("max_amount", "")).strip()
    selected_due_from = (request.GET.get("due_from") or request.POST.get("due_from", "")).strip()
    selected_due_to = (request.GET.get("due_to") or request.POST.get("due_to", "")).strip()
    selected_active = (request.GET.get("active") or request.POST.get("active", "")).strip()
    filter_values = {
        "q": search_query, "course_id": selected_course, "session_id": selected_session,
        "entry_type": selected_entry_type, "semester_id": selected_semester, "title": selected_title,
        "min_amount": selected_min_amount, "max_amount": selected_max_amount,
        "due_from": selected_due_from, "due_to": selected_due_to, "active": selected_active,
    }
    filters = {key: value for key, value in filter_values.items() if value}
    return_to = reverse("admin_fees") + (f"?{urlencode(filters)}" if filters else "")
    form = FeeStructureForm(request.POST or None)
    if request.method == "POST" and request.POST.get("action") == "create_fee":
        if form.is_valid():
            fee = form.save(commit=False)
            if fee.session_id and fee.semester_id:
                fee.due_date = semester_fee_due_date(fee.session, fee.semester)
            fee.save()
            messages.success(request, "Fee item created.")
            return redirect(return_to)
    if request.method == "POST" and request.POST.get("action") == "update_fee":
        fee = get_object_or_404(FeeStructure, pk=request.POST.get("fee_id"))
        if fee.payments.filter(status__in=(FeePayment.Status.PAID, FeePayment.Status.PENDING)).exists():
            messages.error(request, "A fee with a submitted or recorded payment cannot be edited. Create a new fee item for future corrections.")
            return redirect(return_to)
        try:
            fee.amount = Decimal(request.POST.get("amount", ""))
            fee.due_date = semester_fee_due_date(fee.session, fee.semester) if fee.session_id and fee.semester_id else parse_date(request.POST.get("due_date", ""))
            if fee.amount < 0 or fee.due_date is None:
                raise ValueError
            fee.is_active = request.POST.get("is_active") == "on"
            fee.save(update_fields=("amount", "due_date", "is_active"))
            if fee.semester_id:
                fee.semester.fee_estimate = fee.amount
                fee.semester.save(update_fields=("fee_estimate",))
            messages.success(request, "Fee amount and due date updated.")
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Enter a valid non-negative amount and due date.")
        return redirect(return_to)
    fee_rows = FeeStructure.objects.select_related("course", "session", "semester").order_by("course__name", "semester__number")
    if selected_course.isdigit():
        fee_rows = fee_rows.filter(course_id=int(selected_course))
    else:
        selected_course = ""
    if selected_session.isdigit():
        fee_rows = fee_rows.filter(session_id=int(selected_session))
    else:
        selected_session = ""
    if selected_entry_type in FeeStructure.EntryType.values:
        fee_rows = fee_rows.filter(entry_type=selected_entry_type)
    else:
        selected_entry_type = ""
    if selected_semester.isdigit():
        fee_rows = fee_rows.filter(semester_id=int(selected_semester))
    else:
        selected_semester = ""
    if search_query:
        fee_rows = fee_rows.filter(
            Q(title__icontains=search_query) | Q(course__name__icontains=search_query) |
            Q(semester__name__icontains=search_query) | Q(session__start_year__icontains=search_query)
        )
    if selected_title:
        fee_rows = fee_rows.filter(title__icontains=selected_title)
    try:
        min_amount = Decimal(selected_min_amount) if selected_min_amount else None
        max_amount = Decimal(selected_max_amount) if selected_max_amount else None
        if (min_amount is not None and not min_amount.is_finite()) or (max_amount is not None and not max_amount.is_finite()):
            raise InvalidOperation
        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise InvalidOperation
        if min_amount is not None:
            fee_rows = fee_rows.filter(amount__gte=min_amount)
        if max_amount is not None:
            fee_rows = fee_rows.filter(amount__lte=max_amount)
    except (InvalidOperation, ValueError):
        selected_min_amount = selected_max_amount = ""
    due_from = parse_date(selected_due_from) if selected_due_from else None
    due_to = parse_date(selected_due_to) if selected_due_to else None
    if due_from:
        fee_rows = fee_rows.filter(due_date__gte=due_from)
    if due_to:
        fee_rows = fee_rows.filter(due_date__lte=due_to)
    if selected_active in {"yes", "no"}:
        fee_rows = fee_rows.filter(is_active=(selected_active == "yes"))
    course_fee_total = None
    summary_session = None
    selected_course_obj = None
    if selected_course:
        selected_course_obj = Course.objects.filter(pk=int(selected_course)).first()
        summary_fees = FeeStructure.objects.filter(course_id=int(selected_course), is_active=True)
        summary_fees = summary_fees.filter(entry_type=selected_entry_type or FeeStructure.EntryType.REGULAR)
        if selected_session.isdigit():
            summary_fees = summary_fees.filter(session_id=int(selected_session))
            summary_session = Session.objects.filter(pk=int(selected_session)).first()
        else:
            first_session_id = summary_fees.exclude(session__isnull=True).order_by("session__start_year").values_list("session_id", flat=True).first()
            if first_session_id:
                summary_fees = summary_fees.filter(session_id=first_session_id)
                summary_session = Session.objects.filter(pk=first_session_id).first()
            else:
                summary_fees = summary_fees.filter(session__isnull=True)
        course_fee_total = summary_fees.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    fee_page = Paginator(fee_rows, 50).get_page(request.GET.get("page"))
    courses = list(Course.objects.order_by("name"))
    sessions = list(Session.objects.order_by("start_year"))
    semesters = list(Semester.objects.select_related("course").order_by("course__name", "number"))
    # Reuse these small catalog lists for both the filter controls and form
    # options instead of issuing another query per ModelChoiceField.
    for field_name, options in (("course", courses), ("session", sessions), ("semester", semesters)):
        field = form.fields[field_name]
        field.choices = [("", field.empty_label or "---------"), *((item.pk, str(item)) for item in options)]

    return render(request, "hod_template/fees.html", {
        "page_title": "Fees Management", "form": form, "fee_structures": fee_page, "search_query": search_query,
        "courses": courses,
        "sessions": sessions,
        "semesters": semesters,
        "selected_course": selected_course, "selected_session": selected_session,
        "selected_entry_type": selected_entry_type, "entry_type_choices": FeeStructure.EntryType.choices,
        "selected_semester": selected_semester, "selected_title": selected_title,
        "selected_min_amount": selected_min_amount, "selected_max_amount": selected_max_amount,
        "selected_due_from": selected_due_from, "selected_due_to": selected_due_to,
        "selected_active": selected_active, "filters": filters,
        "course_fee_total": course_fee_total, "summary_session": summary_session,
        "selected_course_obj": selected_course_obj,
    })


@role_required("1")
def admin_payment_reviews(request):
    search_query = (request.GET.get("q") or request.POST.get("q", "")).strip()
    student_lookup = (request.GET.get("student_lookup") or "").strip()
    selected_cash_student = (request.GET.get("cash_student") or request.POST.get("cash_student", "")).strip()
    selected_cash_course = (request.GET.get("cash_course") or request.POST.get("cash_course", "")).strip()
    selected_cash_session = (request.GET.get("cash_session") or request.POST.get("cash_session", "")).strip()
    selected_status = (request.GET.get("status") or request.POST.get("status", "pending")).strip()
    valid_statuses = {choice for choice, _label in FeePayment.Status.choices}
    if selected_status not in valid_statuses | {"all"}:
        selected_status = FeePayment.Status.PENDING
    cash_student = None
    cash_course = None
    cash_session = None
    cashable_payments = FeePayment.objects.none()
    if student_lookup:
        email_match = student_lookup.rsplit("—", 1)[-1].strip()
        if "@" in email_match:
            selected_student = Student.objects.filter(admin__email__iexact=email_match).first()
            if selected_student:
                selected_cash_student = str(selected_student.pk)
    if selected_cash_student.isdigit():
        cash_student = Student.objects.select_related("admin", "course", "session").filter(pk=int(selected_cash_student)).first()
        if cash_student and cash_student.course_id and cash_student.session_id:
            selected_cash_course = selected_cash_course or str(cash_student.course_id)
            selected_cash_session = selected_cash_session or str(cash_student.session_id)
            if selected_cash_course.isdigit():
                cash_course = Course.objects.filter(pk=int(selected_cash_course), is_active=True).first()
            if selected_cash_session.isdigit():
                cash_session = Session.objects.filter(pk=int(selected_cash_session)).first()
            if cash_course and cash_session and cash_student.course_id == cash_course.pk and cash_student.session_id == cash_session.pk:
                cash_fees = FeeStructure.objects.filter(course=cash_course, session=cash_session, entry_type=cash_student.admission_type, is_active=True)
            else:
                cash_fees = FeeStructure.objects.none()
            cash_fee_ids = list(cash_fees.values_list("pk", flat=True))
            existing_cash_fee_ids = set(FeePayment.objects.filter(student=cash_student, fee_id__in=cash_fee_ids).values_list("fee_id", flat=True))
            FeePayment.objects.bulk_create(
                [FeePayment(student=cash_student, fee_id=fee_id) for fee_id in cash_fee_ids if fee_id not in existing_cash_fee_ids],
                ignore_conflicts=True,
            )
            if cash_fee_ids:
                cashable_payments = FeePayment.objects.filter(
                    student=cash_student, fee_id__in=cash_fee_ids,
                ).select_related("fee", "fee__course", "fee__session", "fee__semester").order_by("fee__semester__number", "fee__due_date")
        else:
            cash_student = None
            selected_cash_student = ""
    if request.method == "POST" and request.POST.get("action") == "record_cash_payment":
        payment = get_object_or_404(
            FeePayment.objects.select_related("fee", "student"),
            pk=request.POST.get("payment_id"), student_id=request.POST.get("cash_student"),
            fee__course_id=request.POST.get("cash_course"), fee__session_id=request.POST.get("cash_session"),
            fee__is_active=True,
        )
        if payment.status == FeePayment.Status.PAID:
            messages.warning(request, "This fee is already marked as paid.")
        elif not payment.student.course_id or payment.fee.course_id != payment.student.course_id:
            messages.error(request, "The selected fee does not belong to this student's course.")
        elif payment.student.session_id and payment.fee.session_id not in (None, payment.student.session_id):
            messages.error(request, "The selected fee does not match this student's session.")
        elif not payment.fee.is_active:
            messages.error(request, "This fee schedule is not active.")
        else:
            receipt = request.POST.get("receipt_reference", "").strip()
            payment.status = FeePayment.Status.PAID
            payment.payment_reference = f"CASH-{receipt}"[:120] if receipt else f"CASH-{timezone.localdate():%Y%m%d}-{secrets.token_hex(3).upper()}"
            payment.submitted_at = timezone.now()
            payment.reviewed_at = timezone.now()
            payment.reviewed_by = request.user
            payment.admin_note = "Cash received in person and recorded by Admin."
            payment.save(update_fields=("status", "payment_reference", "submitted_at", "reviewed_at", "reviewed_by", "admin_note"))
            messages.success(request, "Cash payment recorded and marked as paid.")
        params = {key: value for key, value in {
            "q": search_query, "cash_student": request.POST.get("cash_student", ""),
            "cash_course": request.POST.get("cash_course", ""),
            "cash_session": request.POST.get("cash_session", ""), "status": selected_status,
        }.items() if value}
        return redirect(reverse("admin_payment_reviews") + (f"?{urlencode(params)}" if params else ""))

    if request.method == "POST" and request.POST.get("action") == "update_payment_status":
        payment = get_object_or_404(FeePayment, pk=request.POST.get("payment_id"))
        new_status = request.POST.get("new_status")
        if new_status not in valid_statuses:
            messages.error(request, "Choose a valid payment status.")
        elif payment.status == FeePayment.Status.PAID and new_status == FeePayment.Status.PAID:
            messages.info(request, "This fee is already marked as paid.")
        else:
            payment.status = new_status
            if new_status in (FeePayment.Status.PENDING, FeePayment.Status.UNPAID):
                payment.reviewed_by = None
                payment.reviewed_at = None
                if new_status == FeePayment.Status.PENDING and not payment.submitted_at:
                    payment.submitted_at = timezone.now()
            else:
                payment.reviewed_by = request.user
                payment.reviewed_at = timezone.now()
            if request.POST.get("admin_note", "").strip():
                payment.admin_note = request.POST.get("admin_note", "").strip()
            payment.save(update_fields=("status", "reviewed_by", "reviewed_at", "submitted_at", "admin_note"))
            messages.success(request, "Payment status updated.")
        params = {key: value for key, value in {
            "q": search_query, "cash_student": selected_cash_student,
            "cash_course": selected_cash_course, "cash_session": selected_cash_session,
            "status": selected_status,
        }.items() if value}
        return redirect(reverse("admin_payment_reviews") + (f"?{urlencode(params)}" if params else ""))

    if request.method == "POST" and request.POST.get("action") == "review_payment":
        payment = get_object_or_404(FeePayment, pk=request.POST.get("payment_id"))
        decision = request.POST.get("decision")
        if payment.status != FeePayment.Status.PENDING:
            messages.warning(request, "Only pending payments can be reviewed.")
        elif decision not in {FeePayment.Status.PAID, FeePayment.Status.REJECTED}:
            messages.error(request, "Choose a valid payment decision.")
        else:
            payment.status = decision
            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.admin_note = request.POST.get("admin_note", "").strip()
            payment.save(update_fields=("status", "reviewed_by", "reviewed_at", "admin_note"))
            messages.success(request, "Payment record updated.")
        params = {key: value for key, value in {
            "q": search_query, "cash_student": selected_cash_student,
            "cash_course": selected_cash_course, "cash_session": selected_cash_session,
            "status": selected_status,
        }.items() if value}
        return redirect(reverse("admin_payment_reviews") + (f"?{urlencode(params)}" if params else ""))

    payments = FeePayment.objects.select_related(
        "student__admin", "fee", "fee__course", "fee__semester", "fee__session"
    ).order_by("-submitted_at", "-pk")
    if selected_status != "all":
        payments = payments.filter(status=selected_status)
    if search_query:
        payments = payments.filter(
            Q(student__admin__first_name__icontains=search_query) |
            Q(student__admin__last_name__icontains=search_query) |
            Q(student__admin__email__icontains=search_query) |
            Q(fee__title__icontains=search_query) | Q(fee__course__name__icontains=search_query) |
            Q(fee__semester__name__icontains=search_query) | Q(payment_reference__icontains=search_query)
        )
    payment_page = Paginator(payments, 50).get_page(request.GET.get("page"))
    return render(request, "hod_template/payment_reviews.html", {
        "page_title": "Fee Payment Reviews", "payments": payment_page,
        "search_query": search_query, "selected_status": selected_status,
        "status_choices": (("all", "All statuses"), *FeePayment.Status.choices),
        "students": Student.objects.select_related("admin", "course").filter(course__isnull=False).order_by("admin__first_name", "admin__last_name"),
        "courses": Course.objects.filter(is_active=True).order_by("name"),
        "sessions": Session.objects.order_by("start_year"),
        "cash_student": cash_student, "cash_course": cash_course, "cash_session": cash_session,
        "selected_cash_student": selected_cash_student, "selected_cash_course": selected_cash_course,
        "selected_cash_session": selected_cash_session,
        "student_lookup": f"{cash_student.admin.get_full_name()} — {cash_student.admin.email}" if cash_student else student_lookup,
        "cashable_payments": cashable_payments,
    })


@role_required("1")
def admin_salary_payments(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_salary":
            staff = get_object_or_404(Staff, pk=request.POST.get("staff_id"))
            period = (request.POST.get("pay_period") or "").strip()
            try:
                amount = Decimal((request.POST.get("amount") or "").strip())
            except (InvalidOperation, ValueError):
                amount = Decimal("0")
            valid_period = bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period))
            if not valid_period or amount <= 0 or amount.as_tuple().exponent < -2:
                messages.error(request, "Enter a valid salary month and a positive amount with at most two decimal places.")
            else:
                profile, _ = TeacherPayrollProfile.objects.get_or_create(
                    staff=staff,
                    defaults={"account_number": f"VTU-DEMO-{staff.pk:06d}"},
                )
                try:
                    SalaryPayment.objects.create(
                        staff=staff, pay_period=period, amount=amount,
                        account_number=profile.account_number,
                    )
                    messages.success(request, "Demo salary payment was added for Payment Department approval.")
                except IntegrityError:
                    messages.error(request, "A salary record already exists for this teacher and month.")
        elif action in {"approve_salary", "reject_salary"}:
            with transaction.atomic():
                payment = get_object_or_404(
                    SalaryPayment.objects.select_for_update().select_related("staff__admin"),
                    pk=request.POST.get("salary_id"),
                )
                if payment.status != SalaryPayment.Status.PENDING:
                    messages.warning(request, "Only pending salary records can be reviewed.")
                else:
                    payment.status = SalaryPayment.Status.PAID if action == "approve_salary" else SalaryPayment.Status.REJECTED
                    payment.reviewed_by = request.user
                    payment.reviewed_at = timezone.now()
                    if action == "approve_salary":
                        payment.payment_reference = f"VTU-DEMO-SAL-{payment.pay_period.replace('-', '')}-{payment.pk:06d}"
                        messages.success(request, "Demo payout approved. No money was transferred.")
                    else:
                        messages.success(request, "Salary record rejected.")
                    payment.save(update_fields=("status", "reviewed_by", "reviewed_at", "payment_reference"))
        return redirect("admin_salary_payments")

    query = (request.GET.get("q") or "").strip()
    status = request.GET.get("status", "all")
    payments = SalaryPayment.objects.select_related("staff__admin", "reviewed_by").order_by("-pay_period", "staff__admin__first_name", "staff__admin__last_name")
    if status in SalaryPayment.Status.values:
        payments = payments.filter(status=status)
    else:
        status = "all"
    if query:
        payments = payments.filter(
            Q(staff__admin__first_name__icontains=query) |
            Q(staff__admin__last_name__icontains=query) |
            Q(staff__admin__email__icontains=query) |
            Q(pay_period__icontains=query) | Q(payment_reference__icontains=query)
        )
    return render(request, "hod_template/salary_payments.html", {
        "page_title": "Teacher Salary Payments",
        "teachers": Staff.objects.select_related("admin").order_by("admin__first_name", "admin__last_name"),
        "payments": Paginator(payments, 40).get_page(request.GET.get("page")),
        "search_query": query,
        "selected_status": status,
        "status_choices": (("all", "All statuses"), *SalaryPayment.Status.choices),
    })


@role_required("2")
def teacher_salary_payments(request):
    staff = get_object_or_404(Staff, admin=request.user)
    profile, _ = TeacherPayrollProfile.objects.get_or_create(
        staff=staff,
        defaults={"account_number": f"VTU-DEMO-{staff.pk:06d}"},
    )
    payments = SalaryPayment.objects.filter(staff=staff).select_related("reviewed_by")
    return render(request, "staff_template/salary_payments.html", {
        "page_title": "My Salary",
        "profile": profile,
        "payments": Paginator(payments, 30).get_page(request.GET.get("page")),
    })


@login_required
def salary_payment_receipt(request, salary_id):
    payment = get_object_or_404(
        SalaryPayment.objects.select_related("staff__admin", "reviewed_by"),
        pk=salary_id, status=SalaryPayment.Status.PAID,
    )
    if request.user.user_type == "2":
        if payment.staff.admin_id != request.user.pk:
            raise Http404
    elif request.user.user_type != "1":
        raise Http404

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    receipt_number = payment.payment_reference or f"VTU-DEMO-SAL-{payment.pk:06d}"
    generated_at = timezone.localtime(payment.reviewed_at or payment.created_at)
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"{receipt_number} - Velocity Tech University",
        author="Velocity Tech University",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SalaryUniversity", parent=styles["Title"], fontName="Times-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#244b8f"), alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="SalaryCell", parent=styles["BodyText"], fontSize=10, leading=14))
    crest_path = settings.BASE_DIR / "main_app" / "static" / "dist" / "img" / "velocity-tech-crest.png"
    story = [Image(str(crest_path), width=28*mm, height=28*mm, kind="proportional"), Spacer(1, 2*mm), Paragraph("VELOCITY TECH UNIVERSITY", styles["SalaryUniversity"]), Paragraph("DEMO SALARY PAYMENT RECEIPT", styles["Heading2"]), Spacer(1, 6*mm)]
    rows = [
        ["Receipt reference", receipt_number],
        ["Teacher", payment.staff.admin.get_full_name() or payment.staff.admin.email],
        ["Email", payment.staff.admin.email],
        ["Salary month", payment.pay_period],
        ["Amount", f"INR {payment.amount:,.2f}"],
        ["Payment status", "PAID — DEMO ONLY"],
        ["Demo account", payment.account_number],
        ["Approved by", payment.reviewed_by.get_full_name() if payment.reviewed_by else "Payment Department"],
        ["Approved on", generated_at.strftime("%d %b %Y, %I:%M %p")],
    ]
    table = Table([[Paragraph(escape(str(a)), styles["SalaryCell"]), Paragraph(escape(str(b)), styles["SalaryCell"])] for a, b in rows], colWidths=[48*mm, 112*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3ff")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#bdc8df")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8deeb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([table, Spacer(1, 10*mm), Paragraph("This is a system-generated demonstration receipt. It records an internal demo payout only; no real bank transfer or money movement occurred.", styles["BodyText"])])
    document.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    disposition = "inline" if request.GET.get("print") == "1" else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{receipt_number}.pdf"'
    return response


def _amount_in_words(amount):
    small = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
    tens = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")

    def under_thousand(number):
        words = []
        if number >= 100:
            words.extend((small[number // 100], "hundred"))
            number %= 100
        if number >= 20:
            words.append(tens[number // 10])
            if number % 10:
                words.append(small[number % 10])
        elif number:
            words.append(small[number])
        return " ".join(words)

    whole = int(amount)
    paise = int((amount - whole) * 100)
    groups = ((10_000_000, "crore"), (100_000, "lakh"), (1_000, "thousand"))
    words = []
    remaining = whole
    for divisor, label in groups:
        count, remaining = divmod(remaining, divisor)
        if count:
            words.extend((under_thousand(count), label))
    if remaining:
        words.append(under_thousand(remaining))
    result = " ".join(words) or "zero"
    if paise:
        result += f" and {under_thousand(paise)} paise"
    return f"Rupees {result} only".title()


@login_required
def fee_payment_receipt(request, payment_id):
    payment = get_object_or_404(
        FeePayment.objects.select_related(
            "student__admin", "student__course", "student__session", "fee__course", "fee__session", "fee__semester", "reviewed_by"
        ),
        pk=payment_id, status=FeePayment.Status.PAID,
    )
    if request.user.user_type == "3":
        if payment.student.admin_id != request.user.pk:
            raise Http404
    elif request.user.user_type != "1":
        raise Http404

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    amount = payment.fee.amount
    paid_at = timezone.localtime(payment.reviewed_at or payment.submitted_at or timezone.now())
    receipt_number = f"VTU-{paid_at:%Y}-{payment.pk:06d}"
    reference = payment.payment_reference or "ADMIN-APPROVED"
    if reference.upper().startswith("CASH-"):
        method = "Cash"
    elif reference.upper().startswith("DEMO-"):
        method = f"{reference.split('-', 2)[1].title()} (Demo)"
    else:
        method = "Admin verified"

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=16 * mm,
        title=f"{receipt_number} - Velocity Tech University",
        author="Velocity Tech University",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="University", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#3159c9"), alignment=TA_CENTER, spaceAfter=3))
    styles.add(ParagraphStyle(name="ReceiptTitle", parent=styles["Heading2"], fontSize=12, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#28324a"), spaceAfter=12))
    styles.add(ParagraphStyle(name="Cell", parent=styles["BodyText"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="HeaderCell", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.white, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SmallCell", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#5d6677")))
    styles.add(ParagraphStyle(name="RightCell", parent=styles["BodyText"], fontSize=9, leading=12, alignment=TA_RIGHT))
    # Use the same university crest shown beside users' names in the dashboard.
    crest_path = settings.BASE_DIR / "main_app" / "static" / "dist" / "img" / "velocity-tech-crest.png"
    crest = Image(str(crest_path), width=25 * mm, height=25 * mm, kind="proportional")
    crest.hAlign = "CENTER"
    story = [
        crest,
        Spacer(1, 1.5 * mm),
        Paragraph("VELOCITY TECH UNIVERSITY", styles["University"]),
        Paragraph("OFFICIAL FEE PAYMENT RECEIPT", styles["ReceiptTitle"]),
    ]
    receipt_meta = Table([
        [Paragraph("Receipt No.", styles["Cell"]), Paragraph(escape(receipt_number), styles["Cell"]), Paragraph("Payment Date", styles["Cell"]), Paragraph(paid_at.strftime("%d %b %Y, %I:%M %p"), styles["Cell"])],
        [Paragraph("Payment Status", styles["Cell"]), Paragraph("PAID / APPROVED", styles["Cell"]), Paragraph("Payment Method", styles["Cell"]), Paragraph(escape(method), styles["Cell"])],
    ], colWidths=[30*mm, 57*mm, 30*mm, 57*mm])
    receipt_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3ff")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef3ff")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bdc8df")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8deeb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend((receipt_meta, Spacer(1, 8*mm), Paragraph("STUDENT DETAILS", styles["Heading3"])))
    student_name = payment.student.admin.get_full_name() or payment.student.admin.email
    course = payment.student.course or payment.fee.course
    session = payment.student.session or payment.fee.session
    semester_name = payment.fee.semester.name if payment.fee.semester_id else "-"
    student_rows = [
        ["Portal Student ID", f"VTU-STU-{payment.student_id:05d}", "Student Name", student_name],
        ["Email", payment.student.admin.email, "Course", course.name],
        ["Academic Session", str(session) if session else "-", "Semester", semester_name],
    ]
    student_table = Table([[Paragraph(escape(str(x)), styles["Cell"]) for x in row] for row in student_rows], colWidths=[30*mm, 57*mm, 30*mm, 57*mm])
    student_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f7fb")), ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f5f7fb")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bdc8df")), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8deeb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend((student_table, Spacer(1, 8*mm), Paragraph("PAYMENT PARTICULARS", styles["Heading3"])))
    details = Table([
        [Paragraph("Particulars", styles["HeaderCell"]), Paragraph("Due Date", styles["HeaderCell"]), Paragraph("Amount Received (INR)", styles["HeaderCell"])],
        [Paragraph(escape(payment.fee.title), styles["Cell"]), Paragraph(payment.fee.due_date.strftime("%d %b %Y"), styles["Cell"]), Paragraph(f"{amount:,.2f}", styles["RightCell"])],
        [Paragraph("Total received", styles["Cell"]), "", Paragraph(f"{amount:,.2f}", styles["RightCell"])],
    ], colWidths=[86*mm, 42*mm, 46*mm])
    details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3159c9")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eef3ff")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bdc8df")), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8deeb")),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.extend((details, Spacer(1, 5*mm), Paragraph(f"Amount in words: <b>{escape(_amount_in_words(amount))}</b>", styles["Cell"]), Spacer(1, 3*mm)))
    payment_info = Table([
        [Paragraph("Payment Reference", styles["Cell"]), Paragraph(escape(reference), styles["Cell"])],
        [Paragraph("Approved By", styles["Cell"]), Paragraph("Velocity Tech University Administration", styles["Cell"])],
    ], colWidths=[38*mm, 136*mm])
    payment_info.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f7fb")), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bdc8df")), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8deeb")), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.extend((payment_info, Spacer(1, 8*mm)))
    signature_path = settings.BASE_DIR / "main_app" / "static" / "image" / "admin-signature.jpg"
    signature = Image(str(signature_path), width=48*mm, height=19*mm, kind="proportional") if signature_path.exists() else Paragraph("Approved", styles["Cell"])
    sign_table = Table([["", signature], ["", Paragraph("Authorized Admin Signature", styles["SmallCell"]) ]], colWidths=[110*mm, 64*mm], rowHeights=[21*mm, 7*mm])
    sign_table.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.extend((sign_table, Spacer(1, 4*mm), Paragraph("This system-generated receipt confirms that the payment is recorded as paid in Velocity Tech University records.", styles["SmallCell"])))
    document.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    disposition = "inline" if request.GET.get("print") == "1" else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{receipt_number}.pdf"'
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@role_required("1")
def admin_teacher_assignments(request):
    return redirect("manage_subject")


@role_required("1")
def admin_semesters(request):
    courses = Course.objects.filter(is_active=True).order_by("name")
    selected_course = request.POST.get("course_id") or request.GET.get("course_id")
    if request.method == "POST" and request.POST.get("action") == "update_semester":
        semester = get_object_or_404(Semester, pk=request.POST.get("semester_id"))
        try:
            amount = Decimal(request.POST.get("fee_estimate", ""))
            name = request.POST.get("name", "").strip()[:80]
            if amount < 0 or not name:
                raise ValueError
            semester.name = name
            semester.fee_estimate = amount
            semester.is_active = request.POST.get("is_active") == "on"
            semester.save(update_fields=("name", "fee_estimate", "is_active"))
            FeeStructure.objects.filter(semester=semester).exclude(payments__status__in=("paid", "pending")).update(amount=amount)
            messages.success(request, "Semester plan updated. Unpaid fee rows were synchronized.")
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Enter a valid semester name and non-negative amount.")
        return redirect(f"{reverse('admin_semesters')}?course_id={semester.course_id}")
    semesters = Semester.objects.none()
    if selected_course:
        semesters = Semester.objects.filter(course_id=selected_course).select_related("course").prefetch_related("subjects__staff__admin", "subjects__co_teachers__admin").order_by("number")
    return render(request, "hod_template/semesters.html", {
        "page_title": "Semester Plans", "courses": courses,
        "selected_course": str(selected_course or ""), "semesters": semesters,
    })


@role_required("1")
def admin_teacher_attendance(request):
    if request.method == "POST":
        record = get_object_or_404(TeacherAttendance, pk=request.POST.get("record_id"))
        action = request.POST.get("action")
        if action == "delete":
            record.delete()
            messages.success(request, "Teacher attendance record removed.")
            return redirect("admin_teacher_attendance")
        if action == "update":
            work_date = parse_date(request.POST.get("work_date", ""))
            check_in = parse_datetime(request.POST.get("checked_in_at", "")) if request.POST.get("checked_in_at") else None
            check_out = parse_datetime(request.POST.get("checked_out_at", "")) if request.POST.get("checked_out_at") else None
            duplicate_day = work_date and TeacherAttendance.objects.filter(
                staff=record.staff, work_date=work_date
            ).exclude(pk=record.pk).exists()
            if not work_date or duplicate_day or (check_in and check_out and check_out <= check_in):
                messages.error(request, "Use a unique date for this teacher and ensure check-out is after check-in.")
            else:
                record.work_date = work_date
                record.checked_in_at = timezone.make_aware(check_in) if check_in and timezone.is_naive(check_in) else check_in
                record.checked_out_at = timezone.make_aware(check_out) if check_out and timezone.is_naive(check_out) else check_out
                record.note = request.POST.get("note", "").strip()[:240]
                record.save(update_fields=("work_date", "checked_in_at", "checked_out_at", "note", "updated_at"))
                messages.success(request, "Teacher attendance record updated.")
            return redirect("admin_teacher_attendance")
    records = TeacherAttendance.objects.select_related("staff__admin", "staff__course")
    work_date = request.GET.get("date", "").strip()
    search_query = request.GET.get("q", "").strip()
    if work_date:
        records = records.filter(work_date=work_date)
    if search_query:
        records = records.filter(
            Q(staff__admin__first_name__icontains=search_query) |
            Q(staff__admin__last_name__icontains=search_query) |
            Q(staff__admin__email__icontains=search_query) |
            Q(staff__course__name__icontains=search_query) | Q(note__icontains=search_query)
        )
    records = Paginator(records.order_by("-work_date", "-checked_in_at"), 50).get_page(request.GET.get("page"))
    return render(request, "hod_template/teacher_attendance.html", {
        "page_title": "Teacher Attendance", "records": records, "search_query": search_query,
        "work_date": work_date,
    })


@role_required("1", "2", "3")
def notice_board(request):
    role = str(request.user.user_type)
    audience = {"2": "teachers", "3": "students"}.get(role)
    notices = Notice.objects.filter(published=True)
    if audience:
        notices = notices.filter(audience__in=("everyone", audience))
    notices = notices.select_related("created_by")
    return render(request, "main_app/notice_board.html", {"page_title": "Notice Board", "notices": notices})


@role_required("1")
def manage_notices(request):
    form = NoticeForm(request.POST or None)
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            get_object_or_404(Notice, pk=request.POST.get("notice_id")).delete()
            messages.success(request, "Notice removed from the board.")
            return redirect("manage_notices")
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, "Notice published.")
            return redirect("manage_notices")
    return render(request, "hod_template/notices.html", {
        "page_title": "Manage Notices", "form": form,
        "notices": Notice.objects.select_related("created_by"),
    })


def _resources_visible_to(user):
    role = str(user.user_type)
    resources = CollegeResource.objects.select_related("uploaded_by", "course", "semester")
    if role == "1":
        return resources
    if role == "2":
        try:
            course_id = user.staff.course_id
        except Staff.DoesNotExist:
            course_id = None
        visible = Q(audience=CollegeResource.Audience.TEACHERS)
        if course_id:
            visible |= Q(audience=CollegeResource.Audience.STUDENTS) & (Q(course_id=course_id) | Q(course__isnull=True))
        else:
            visible |= Q(audience=CollegeResource.Audience.STUDENTS, course__isnull=True)
        return resources.filter(is_active=True).filter(visible)
    try:
        course_id = user.student.course_id
        semester_id = user.student.semester_id
    except Student.DoesNotExist:
        course_id = None
        semester_id = None
    course_scope = Q(course__isnull=True)
    semester_scope = Q(semester__isnull=True)
    if course_id:
        course_scope |= Q(course_id=course_id)
    if semester_id:
        semester_scope |= Q(semester_id=semester_id)
    visible = Q(audience=CollegeResource.Audience.STUDENTS) & course_scope & semester_scope
    return resources.filter(is_active=True).filter(visible)


def _resource_list_context(request, role):
    resources = _resources_visible_to(request.user)
    query = request.GET.get("q", "").strip()
    if query:
        resources = resources.filter(
            Q(title__icontains=query) | Q(description__icontains=query) |
            Q(course__name__icontains=query) | Q(semester__name__icontains=query) |
            Q(subject__name__icontains=query)
        )
    return {
        "page_title": "Learning Resources",
        "resources": Paginator(resources, 25).get_page(request.GET.get("page")),
        "search_query": query,
        "can_upload": role in ("1", "2"),
        "is_admin": role == "1",
        "is_teacher": role == "2",
    }


@role_required("1", "2")
def manage_books(request, book_id=None):
    book = get_object_or_404(Book, pk=book_id) if book_id else None
    form = BookForm(request.POST or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Book details updated." if book else "Book added to the library.")
        return redirect("manage_books")
    return render(request, "main_app/manage_books.html", {
        "form": form,
        "books": Book.objects.order_by("name", "author"),
        "editing_book": book,
    })


def _grade_cards_visible_to(user):
    cards = StudentGradeCard.objects.select_related(
        "student__admin", "student__course", "student__session", "semester__course", "uploaded_by",
    )
    role = str(user.user_type)
    if role == "1":
        return cards
    if role == "2":
        assigned = Q(semester__subjects__staff__admin=user) | Q(semester__subjects__co_teachers__admin=user)
        return cards.filter(assigned).distinct()
    if role == "3":
        return cards.filter(student__admin=user)
    return cards.none()


@role_required("1", "2", "3")
def grade_cards(request):
    role = str(request.user.user_type)
    cards = _grade_cards_visible_to(request.user)
    form = None
    editing_card = None
    if role in {"1", "2"}:
        edit_id = request.GET.get("edit")
        if request.method == "POST":
            edit_id = request.POST.get("grade_card_id") or edit_id
        if edit_id:
            editing_card = get_object_or_404(cards, pk=edit_id)
        form = StudentGradeCardForm(
            request.POST or None,
            request.FILES or None,
            instance=editing_card,
            teacher_id=request.user.pk if role == "2" else None,
        )
        if request.method == "POST" and form.is_valid():
            old_file_name = editing_card.file.name if editing_card and editing_card.file else None
            old_file_storage = editing_card.file.storage if editing_card and editing_card.file else None
            grade_card = form.save(commit=False)
            grade_card.uploaded_by = request.user
            grade_card.save()
            if old_file_name and old_file_name != grade_card.file.name:
                old_file_storage.delete(old_file_name)
            messages.success(request, "Grade card updated." if editing_card else "Grade card uploaded.")
            return redirect("grade_cards")

    return render(request, "main_app/grade_cards.html", {
        "form": form,
        "grade_cards": cards,
        "editing_card": editing_card,
        "can_manage": role in {"1", "2"},
        "is_student": role == "3",
    })


@role_required("1", "2", "3")
def download_grade_card(request, grade_card_id):
    grade_card = _grade_cards_visible_to(request.user).filter(pk=grade_card_id).first()
    if not grade_card or not grade_card.file:
        raise Http404("Grade card not found")
    filename = os.path.basename(grade_card.file.name)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    download_name = f"{grade_card.student.admin.get_full_name()}-{grade_card.title}{os.path.splitext(filename)[1]}"
    response = FileResponse(
        grade_card.file.open("rb"), as_attachment=True,
        filename=download_name, content_type=content_type,
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@role_required("1")
def admin_learning_resources(request):
    if request.method == "POST" and request.POST.get("action") == "delete":
        resource = get_object_or_404(CollegeResource, pk=request.POST.get("resource_id"))
        if resource.file:
            resource.file.delete(save=False)
        resource.delete()
        messages.success(request, "The resource was removed.")
        return redirect("admin_learning_resources")
    form = CollegeResourceForm(request.POST or None, request.FILES or None, uploader_role="1")
    if request.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.uploaded_by = request.user
        resource.save()
        messages.success(request, "The resource was uploaded.")
        return redirect("admin_learning_resources")
    context = _resource_list_context(request, "1")
    context["form"] = form
    return render(request, "main_app/learning_resources.html", context)


@role_required("2")
def teacher_learning_resources(request):
    form = CollegeResourceForm(
        request.POST or None, request.FILES or None,
        uploader_role="2", teacher_id=request.user.pk,
    )
    if request.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.course = form.cleaned_data["course"]
        resource.semester = form.cleaned_data["semester"]
        resource.audience = CollegeResource.Audience.STUDENTS
        resource.is_active = True
        resource.uploaded_by = request.user
        resource.save()
        messages.success(request, "The learning resource is now available to students in its selected course.")
        return redirect("teacher_learning_resources")
    context = _resource_list_context(request, "2")
    context["form"] = form
    return render(request, "main_app/learning_resources.html", context)


@role_required("3")
def student_learning_resources(request):
    context = _resource_list_context(request, "3")
    return render(request, "main_app/learning_resources.html", context)


@role_required("1", "2", "3")
def download_learning_resource(request, resource_id):
    resource = _resources_visible_to(request.user).filter(pk=resource_id).first()
    if not resource or not resource.file:
        raise Http404("Resource not found")
    filename = os.path.basename(resource.file.name)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    response = FileResponse(resource.file.open("rb"), as_attachment=True, filename=filename, content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
