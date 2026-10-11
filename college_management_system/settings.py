"""Settings for the Velocity Tech University portal."""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY.startswith("replace-with-"):
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a unique secret in the project .env file.")

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main_app.apps.MainAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main_app.middleware.LoginCheckMiddleWare",
]

ROOT_URLCONF = "college_management_system.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "main_app" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "college_management_system.wsgi.application"
ASGI_APPLICATION = "college_management_system.asgi.application"

database_url = os.environ.get("DATABASE_URL")
if not database_url or "USER:PASSWORD@HOST" in database_url:
    raise ImproperlyConfigured(
        "Set DATABASE_URL to your Neon PostgreSQL connection string in the project .env file."
    )
DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600")),
        conn_health_checks=True,
        ssl_require=not DEBUG,
    )
}
# The configured Neon URL uses the transaction-mode pooler. PostgreSQL
# server-side cursors are connection-local and fail when the pooler assigns a
# different backend connection between fetches.
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
PRIVATE_RESOURCES_ROOT = Path(
    os.environ.get("PRIVATE_RESOURCES_ROOT", BASE_DIR / "private_resources")
)
USE_REMOTE_MEDIA = os.environ.get(
    "USE_REMOTE_MEDIA", "false" if DEBUG else "true"
).lower() in {"1", "true", "yes"}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if USE_REMOTE_MEDIA:
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
    # Neon Object Storage exposes the standard AWS_* variables. Keep the
    # django-storages spellings as fallbacks for existing S3/R2 deployments.
    AWS_S3_ENDPOINT_URL = (
        os.environ.get("AWS_ENDPOINT_URL_S3", "").strip()
        or os.environ.get("AWS_S3_ENDPOINT_URL", "").strip()
        or None
    )
    AWS_S3_REGION_NAME = (
        os.environ.get("AWS_REGION", "").strip()
        or os.environ.get("AWS_S3_REGION_NAME", "").strip()
        or "us-east-1"
    )
    missing_storage_settings = [
        name for name, value in (
            ("AWS_STORAGE_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME),
            ("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID),
            ("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY),
        ) if not value
    ]
    if missing_storage_settings:
        raise ImproperlyConfigured(
            "Remote media storage is enabled. Set these hosting secrets: "
            + ", ".join(missing_storage_settings)
            + ". See DEVELOPER_GUIDE.md."
        )
    INSTALLED_APPS.append("storages")
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
    AWS_LOCATION = "media"
    AWS_DEFAULT_ACL = None  # Bucket policy keeps objects private.
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = os.environ.get(
        "AWS_S3_ADDRESSING_STYLE", "path" if AWS_S3_ENDPOINT_URL else "auto"
    ).strip()

AUTH_USER_MODEL = "main_app.CustomUser"
AUTHENTICATION_BACKENDS = ["main_app.EmailBackend.EmailBackend"]
LOGIN_URL = "login_page"
LOGIN_REDIRECT_URL = "login_page"
LOGOUT_REDIRECT_URL = "login_page"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Velocity Tech University <no-reply@example.com>")


SESSION_IDLE_TIMEOUT_SECONDS = int(os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "300"))
SESSION_COOKIE_AGE = SESSION_IDLE_TIMEOUT_SECONDS
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    # Render terminates TLS at its proxy and forwards the original scheme.
    # Trust that header so Django does not redirect HTTPS requests in a loop.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in {"1", "true", "yes"}
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
