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
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from . import settings

urlpatterns = [
    path("", include('main_app.urls')),
    # The portal has one role-aware sign-in page. Keep legacy Django auth
    # login links from resolving to LoginView's absent default template.
    path("accounts/login/", RedirectView.as_view(url="/", query_string=True), name="accounts_login_redirect"),
    path("accounts/", include("django.contrib.auth.urls")),
    path('admin/', admin.site.urls),
]

# Uploaded files are served from the private object-storage provider in
# production; only local development serves files from MEDIA_ROOT.
if settings.DEBUG and not settings.USE_REMOTE_MEDIA:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
