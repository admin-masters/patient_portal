# pedi_portal/settings/base.py  (only the relevant bits shown)
from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DB_NAME=(str, "pedi_portal"),
    DB_USER=(str, "root"),
    DB_PASSWORD=(str, ""),
    DB_HOST=(str, "127.0.0.1"),
    DB_PORT=(str, "3306"),
    DJANGO_SECRET_KEY=(str, "changeme"),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # our apps
    "core",
    "geo",
    "accounts",
    "clinics",
    "brands",
    "content",
    "registration",
    "campaigns",
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
]

ROOT_URLCONF = "pedi_portal.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

WSGI_APPLICATION = "pedi_portal.wsgi.application"
ASGI_APPLICATION = "pedi_portal.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_ALL_TABLES'",
        },
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# **Local media only** (no S3)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Storage backends (local FS)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/1")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_DEFAULT_QUEUE = "default"

# WhatsApp / Email toggles
WABA_ENABLE = env.bool("WABA_ENABLE", default=False)
WABA_PROVIDER = env("WABA_PROVIDER", default="meta")
WABA_PHONE_NUMBER_ID = env("WABA_PHONE_NUMBER_ID", default="")
WABA_TOKEN = env("WABA_TOKEN", default="")

SENDGRID_ENABLE = env.bool("SENDGRID_ENABLE", default=False)
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
SENDGRID_FROM_EMAIL = env("SENDGRID_FROM_EMAIL", default="no-reply@example.com")
SENDGRID_FROM_NAME = env("SENDGRID_FROM_NAME", default="Patient Education")
