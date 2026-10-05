"""Route users by role and expire portal sessions after five idle minutes."""

import time

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class LoginCheckMiddleWare:
    """Keep the legacy role dashboards isolated while allowing auth setup."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        module = view_func.__module__
        public_paths = {
            reverse("login_page"),
            reverse("user_login"),
            reverse("user_logout"),
            *(reverse("role_login_page", kwargs={"role": role}) for role in ("admin", "teacher", "student")),
            reverse("register_page"),
            *(reverse("role_register_page", kwargs={"role": role}) for role in ("admin", "teacher", "student")),
        }

        try:
            user = request.user
            authenticated = user.is_authenticated
            role = str(getattr(user, "user_type", "")) if authenticated else ""
        except (OperationalError, ProgrammingError):
            return redirect("login_page")

        if authenticated:
            now = time.time()
            idle_timeout = settings.SESSION_IDLE_TIMEOUT_SECONDS
            last_activity = request.session.get("last_activity")
            try:
                expired = last_activity is not None and now - float(last_activity) >= idle_timeout
            except (TypeError, ValueError):
                expired = True
            if expired:
                logout(request)
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    minutes = max(1, round(idle_timeout / 60))
                    return JsonResponse({"error": f"Your session expired after {minutes} minutes of inactivity."}, status=401)
                return redirect("login_page")
            # The heartbeat only reports recent browser activity; it must not
            # extend an idle session by itself.
            if not (request.resolver_match and request.resolver_match.url_name == "session_activity"):
                request.session["last_activity"] = now
            request.session.set_expiry(idle_timeout)

        public_role_route = request.resolver_match and request.resolver_match.url_name in {
            "role_login_page", "role_register_page",
        }
        if request.path in public_paths or public_role_route or module.startswith("django.contrib.auth"):
            return None

        if not authenticated:
            if request.path.startswith("/admin/"):
                return None
            return redirect("login_page")

        if role in {"2", "3"} and request.resolver_match.url_name not in {
            "portal_maintenance", "user_logout", "session_activity",
        }:
            try:
                from .portal_views import portal_access_state
                state = portal_access_state()
                portal_enabled = state["teacher_portal_enabled"] if role == "2" else state["student_portal_enabled"]
            except (OperationalError, ProgrammingError):
                portal_enabled = True
            if not portal_enabled:
                return redirect("portal_maintenance")

        if role == "2":
            try:
                approval_status = user.staff.approval_status
            except (AttributeError, OperationalError, ProgrammingError):
                approval_status = "pending"
            if approval_status != "approved":
                logout(request)
                messages.info(request, "Your Teacher account is not approved for portal access yet.")
                return redirect("role_login_page", role="teacher")

        if module.startswith("main_app.hod_views") and role != "1":
            return redirect(self._dashboard_for(role))
        if module.startswith("main_app.staff_views") and role != "2":
            return redirect(self._dashboard_for(role))
        if module.startswith("main_app.student_views") and role != "3":
            return redirect(self._dashboard_for(role))
        if module.startswith("main_app.EditResultView") and role != "2":
            return redirect(self._dashboard_for(role))

        return None

    @staticmethod
    def _dashboard_for(role):
        return {"1": "admin_home", "2": "staff_home", "3": "student_home"}.get(role, "login_page")
