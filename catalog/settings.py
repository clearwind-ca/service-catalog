import logging
import os
from pathlib import Path

import dj_database_url
from django.contrib.messages import constants as messages
from django.forms.widgets import DateInput, DateTimeInput, SelectMultiple, TimeInput
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = BASE_DIR.joinpath("catalog").joinpath("envs")

if os.environ.get("CI"):
    env = os.environ.get("CATALOG_ENV", "testing")
else:
    env = os.environ.get("CATALOG_ENV", "development")

print(f"✅ Loading {env}.env environment variables")
if env in ["testing", "staging", "development", "production"]:
    env = ENV_DIR.joinpath(f"{env}.env")

if not os.path.exists(env):
    raise FileNotFoundError(f"Unable to find {env} file.")

load_dotenv(dotenv_path=env)

# Doing this so that it shows up in the debug page for clarity.
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(" ")
auth_pwd = "django.contrib.auth.password_validation"
ATOMIC_REQUESTS = True
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{auth_pwd}.UserAttributeSimilarityValidator"},
    {"NAME": f"{auth_pwd}.MinimumLengthValidator"},
    {"NAME": f"{auth_pwd}.CommonPasswordValidator"},
    {"NAME": f"{auth_pwd}.NumericPasswordValidator"},
]
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
CATALOG_ENV = env
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours

# Default timeout 6 hours.
CHECKS_TIMEOUT_HOURS = os.environ.get("CHECKS_TIMEOUT_HOURS", 6)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
DEBUG = os.environ.get("DEBUG")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ENFORCE_ORG_MEMBERSHIP = True
if os.environ.get("CI"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {"default": dj_database_url.config(conn_max_age=600, conn_health_checks=True)}

GITHUB_CHECK_REPOSITORY = os.environ.get("GITHUB_CHECK_REPOSITORY", None)
GITHUB_DEBUG = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_extensions",
    "auditlog",
    "crispy_forms",
    "crispy_bootstrap5",
    "oauthlogin",
    "rest_framework",
    "rest_framework.authtoken",
    "services",
    "health",
    "events",
    "octicons",
    "systemlogs",
    "web",
    "gh",
]
LANGUAGE_CODE = "en-us"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

logging.getLogger("github").setLevel(logging.ERROR)
logging.getLogger("faker").setLevel(logging.ERROR)
logging.getLogger("gh.fetch").setLevel(logging.ERROR)
logging.getLogger("MARKDOWN").setLevel(logging.ERROR)

LOGIN_REQUIRED_IGNORE_PATHS = [
    "/oauth/github/login/",
    "/oauth/github/callback/",
    "^/static/*.*",
]
LOGIN_REQUIRED_IGNORE_VIEW_NAMES = ["web:home", "web:setup", "web:login-problem", "web:logout"]
LOGIN_REQUIRED_REDIRECT_FIELD_NAME = "next"
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/services/"
MESSAGE_TAGS = {
    messages.ERROR: "danger",
    messages.INFO: "primary",
}
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "web.middleware.CatalogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]
OAUTH_LOGIN_PROVIDERS = {
    "github": {
        "class": "web.oauth.GitHubOAuthProvider",
        "kwargs": {
            "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
            "client_secret": os.environ.get("GITHUB_CLIENT_SECRET", ""),
        },
    },
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
ROOT_URLCONF = "catalog.urls"
SERVICE_SCHEMA = os.environ.get(
    "SERVICE_SCHEMA", os.path.join(BASE_DIR, "catalog", "schemas", "service.json")
)
SECRET_KEY = os.environ.get("SECRET_KEY")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SERVER_URL = os.environ.get("SERVER_URL")
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "web", "static"))
STATIC_URL = "static/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.helpers.site_context",
            ],
        },
    },
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
WSGI_APPLICATION = "catalog.wsgi.application"


# Monkeypatch inputs so we get a good HTML date and time picker by default.
if DateInput.input_type != "date":
    DateInput.input_type = "date"

if TimeInput.input_type != "time":
    TimeInput.input_type = "time"

if DateTimeInput.input_type != "datetime-local":
    DateTimeInput.input_type = "datetime-local"
