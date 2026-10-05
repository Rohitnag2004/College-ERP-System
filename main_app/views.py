from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.http import Http404
from django.views.decorators.http import require_POST
from django.conf import settings
import secrets
import re
import time

from .models import Attendance, CustomUser, Session, Subject
from .forms import SelfRegistrationForm


LOGIN_ROLES = {"admin": ("1", "Administrator"), "teacher": ("2", "Teacher"), "student": ("3", "Student")}
ROLE_DESTINATIONS = {"1": "admin_home", "2": "staff_home", "3": "student_home"}


def _new_login_captcha(request):
    left = secrets.randbelow(9) + 1
    right = secrets.randbelow(9) + 1
    request.session["login_captcha_answer"] = str(left + right)
    return f"{left} + {right} = ?"

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        return redirect(ROLE_DESTINATIONS.get(request.user.user_type, "login_page"))
    return render(request, 'main_app/login.html', {
        "login_role": "", "login_role_label": "", "captcha_question": _new_login_captcha(request),
    })


def role_login_page(request, role):
    if role not in LOGIN_ROLES:
        raise Http404("Unknown login role")
    return redirect("login_page")


def register_page(request):
    if request.user.is_authenticated:
        return redirect(ROLE_DESTINATIONS.get(request.user.user_type, "login_page"))
    return render(request, "main_app/signup.html", {"registration_role": "", "registration_role_label": ""})


def role_register_page(request, role):
    if role not in LOGIN_ROLES:
        raise Http404("Unknown registration role")
    if request.user.is_authenticated:
        return redirect(ROLE_DESTINATIONS.get(request.user.user_type, "login_page"))

    admin_signup_closed = role == "admin"
    form = SelfRegistrationForm(request.POST or None)
    if request.method == "POST":
        if admin_signup_closed:
            messages.error(request, "Admin accounts can only be created by an existing administrator.")
        elif form.is_valid():
            try:
                with transaction.atomic():
                    form.create_user(LOGIN_ROLES[role][0])
            except IntegrityError:
                form.add_error("email", "An account with this email address already exists.")
            else:
                if role == "teacher":
                    messages.success(request, "Your Teacher account has been created. An Admin must approve it before you can sign in.")
                else:
                    messages.success(request, "Your Student account is ready. Sign in with your email and password to choose a course.")
                return redirect("role_login_page", role=role)

    return render(request, "main_app/signup.html", {
        "registration_role": role,
        "registration_role_label": LOGIN_ROLES[role][1],
        "admin_signup_closed": admin_signup_closed,
        "form": form,
    })


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    submitted_captcha = request.POST.get("captcha_answer", "").strip()
    expected_captcha = request.session.pop("login_captcha_answer", None)
    if not expected_captcha or not secrets.compare_digest(submitted_captcha, expected_captcha):
        messages.error(request, "The CAPTCHA answer is incorrect. Please try again.")
        return redirect("login_page")

    selected_role = request.POST.get("role", "").strip().lower()
    if selected_role not in LOGIN_ROLES:
        messages.error(request, "Select Admin, Teacher, or Student before signing in.")
        return redirect("login_page")

    user = authenticate(
        request,
        username=request.POST.get("email", "").strip().lower(),
        password=request.POST.get("password", ""),
    )
    if user is None:
        messages.error(request, "The email address or password is incorrect.")
        return redirect("role_login_page", role=selected_role)

    expected_user_type, role_label = LOGIN_ROLES[selected_role]
    if user.user_type != expected_user_type:
        messages.error(request, f"This account is not registered for the {role_label} portal. Select the correct role and try again.")
        return redirect("role_login_page", role=selected_role)

    if user.user_type == "2":
        status = getattr(getattr(user, "staff", None), "approval_status", "pending")
        if status != "approved":
            if status == "rejected":
                messages.error(request, "Your Teacher account was not approved. Please contact the administration.")
            else:
                messages.info(request, "Your Teacher account is awaiting Admin approval. You can sign in after it is approved.")
            return redirect("role_login_page", role=selected_role)

    login(request, user)
    request.session.set_expiry(30 * 24 * 60 * 60 if request.POST.get("remember") else 0)
    destination = ROLE_DESTINATIONS.get(user.user_type)
    if destination is None:
        logout(request)
        messages.error(request, "This account does not have a valid portal role.")
        return redirect("login_page")
    return redirect(destination)



@require_POST
def logout_user(request):
    logout(request)
    return redirect("login_page")


@require_POST
def session_activity(request):
    """Extend the idle timer only when the browser reports recent user input."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Your session has expired."}, status=401)

    now = time.time()
    timeout = settings.SESSION_IDLE_TIMEOUT_SECONDS
    try:
        last_activity = float(request.session.get("last_activity", now))
        reported_activity = float(request.POST.get("last_activity", ""))
    except (TypeError, ValueError):
        logout(request)
        return JsonResponse({"error": "Your session has expired."}, status=401)

    if now - last_activity >= timeout or now - reported_activity >= timeout or reported_activity > now + 30:
        logout(request)
        return JsonResponse({"error": "Your session expired after five minutes of inactivity."}, status=401)

    request.session["last_activity"] = max(last_activity, reported_activity)
    request.session.set_expiry(timeout)
    return JsonResponse({"ok": True})


def get_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    if str(getattr(request.user, "user_type", "")) not in {"1", "2"}:
        return JsonResponse({"error": "You do not have access to attendance records."}, status=403)
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subjects = Subject.objects.all()
        if request.user.user_type == "2":
            subjects = subjects.filter(Q(staff__admin=request.user) | Q(co_teachers__admin=request.user)).distinct()
        subject = get_object_or_404(subjects, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        course_duration = re.search(r"(\d+)", subject.course.duration or "")
        if course_duration and session.end_year.year - session.start_year.year != int(course_duration.group(1)):
            return JsonResponse({"error": "Choose a session matching this course duration."}, status=400)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session_id,
                    "semester": attd.semester_id,
                    }
            attendance_list.append(data)
        return JsonResponse(attendance_list, safe=False)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid attendance selection"}, status=400)


def showFirebaseJS(request):
    return HttpResponse("// Push notifications are not configured for this deployment.\n", content_type="application/javascript")

