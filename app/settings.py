"""
Django settings for the web-data-scrape service.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    """Read a boolean environment variable with predictable parsing."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set.")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", env_bool("DEBUG", False))

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

# Scraping limits (overridable per environment)
SCRAPE_REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("SCRAPE_REQUEST_TIMEOUT_SECONDS", "30")
)
SCRAPE_PAGE_TIMEOUT_MS = int(os.getenv("SCRAPE_PAGE_TIMEOUT_MS", "30000"))
SCRAPE_MAX_HTML_BYTES = int(os.getenv("SCRAPE_MAX_HTML_BYTES", "5000000"))
SCRAPE_MAX_EXTRACTION_DEPTH = int(os.getenv("SCRAPE_MAX_EXTRACTION_DEPTH", "50"))
SCRAPE_MAX_EXTRACTION_NODES = int(os.getenv("SCRAPE_MAX_EXTRACTION_NODES", "10000"))
SCRAPE_MAX_ELEMENTS = int(os.getenv("SCRAPE_MAX_ELEMENTS", "1000"))

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.scrape",
    "app.client_management.apps.ClientManagementConfig",
    "rest_framework",
    "drf_spectacular",
    "channels",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "app.api_exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "scrape": os.getenv("SCRAPE_THROTTLE_RATE", "60/min"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Web Data Scrape API",
    "DESCRIPTION": (
        "Render web pages with Playwright and extract elements by CSS class name."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

SCALAR_TITLE = os.getenv("SCALAR_TITLE", "Web Data Scrape API")
SCALAR_JS_URL = os.getenv(
    "SCALAR_JS_URL",
    "https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.76.0/esm.js",
)

ROOT_URLCONF = "app.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

ASGI_APPLICATION = "app.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", os.getenv("DATABASE_HOST")),
        "PORT": os.getenv("POSTGRES_PORT", os.getenv("DATABASE_PORT", "5432")),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}

# Password validation (optional)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Logging configuration
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        # Avoid duplicate output: let these records propagate to the root
        # handler exactly once.
        "django.request": {
            "handlers": [],
            "level": "WARNING",
            "propagate": True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files (uploaded by users)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
