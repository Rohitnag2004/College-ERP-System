"""college_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.views.static import serve
from . import settings

urlpatterns = [
    path("", include('main_app.urls')),
    # The portal has one role-aware sign-in page. Keep legacy Django auth
    # login links from resolving to LoginView's absent default template.
    path("accounts/login/", RedirectView.as_view(url="/", query_string=True), name="accounts_login_redirect"),
    path("accounts/", include("django.contrib.auth.urls")),
    path('admin/', admin.site.urls),
]

# Profile photos use MEDIA_ROOT when remote media storage is disabled. Keep
# them behind authentication; private learning resources have their own
# role-checked download views and are never served from this route.
if settings.DEBUG and not settings.USE_REMOTE_MEDIA:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif not settings.USE_REMOTE_MEDIA:
    urlpatterns += [
        re_path(
            r"^media/profiles/(?P<path>.*)$",
            login_required(serve),
            {"document_root": settings.MEDIA_ROOT / "profiles"},
        )
    ]
