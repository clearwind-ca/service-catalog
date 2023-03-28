import os
from pathlib import Path

from django.contrib.messages import constants as messages
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_DIR = BASE_DIR.joinpath("catalog").joinpath("envs")

env = os.environ.get("CATALOG_ENV", "development")
print(f"✅ Loading {env}.env environment variables")
load_dotenv(ENV_DIR.joinpath(f"{env}.env"))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(" ")
auth_pwd = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{auth_pwd}.UserAttributeSimilarityValidator"},
    {"NAME": f"{auth_pwd}.MinimumLengthValidator"},
    {"NAME": f"{auth_pwd}.CommonPasswordValidator"},
    {"NAME": f"{auth_pwd}.NumericPasswordValidator"},
]
DEBUG = os.environ.get("DEBUG")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
if os.environ.get("CI"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": os.environ.get("DB_NAME", BASE_DIR.joinpath("db.sqlite3")),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", ""),
            "PORT": os.environ.get("DB_PORT", ""),
        }
    }
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "oauthlogin",
    "services",
    "health",
    "deployments",
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
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/"
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
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
OAUTH_LOGIN_PROVIDERS = {
    "github": {
        "class": "web.oauth.GitHubOAuthProvider",
        "kwargs": {
            "client_id": os.environ["GITHUB_CLIENT_ID"],
            "client_secret": os.environ["GITHUB_CLIENT_SECRET"],
        },
    },
}
ROOT_URLCONF = "catalog.urls"
SERVICE_SCHEMA = os.environ.get(
    "SERVICE_SCHEMA", os.path.join(BASE_DIR, "catalog", "schemas", "schema.json")
)
SECRET_KEY = os.environ.get("SECRET_KEY")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
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
