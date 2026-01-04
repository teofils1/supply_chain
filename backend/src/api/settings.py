"""
Django settings for api project.

Environment-driven configuration using .env at project root (backend/.env).
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # /backend/src

# Load environment variables from backend/.env
load_dotenv(BASE_DIR.parent / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes"}

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
    "model_utils",  # For field change tracking
    "django_celery_beat",  # Celery periodic tasks
    # Local apps
    "supplychain",
]

MIDDLEWARE = [
    "supplychain.middleware.RequestLoggingMiddleware",  # Request/response logging (first)
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "supplychain.middleware.CurrentUserMiddleware",  # Track current user
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"


# Database: PostgreSQL via psycopg using env vars
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", ""),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

# REST framework and JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "supplychain.exceptions.custom_exception_handler",
    # Pagination - configurable page size with sensible defaults
    "DEFAULT_PAGINATION_CLASS": "supplychain.pagination.StandardResultsPagination",
    "PAGE_SIZE": int(os.getenv("API_PAGE_SIZE", "5")),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_LIFETIME_MINUTES", "60"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", "7"))
    ),
}

# CORS
cors_origin = os.getenv("CORS_ORIGIN")
if cors_origin:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origin.split(",") if o.strip()]
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG

# CSRF trusted origins (optional, useful in dev when using a separate frontend)
if cors_origin:
    CSRF_TRUSTED_ORIGINS = [
        o.replace("http://", "http://").replace("https://", "https://")
        for o in CORS_ALLOWED_ORIGINS
    ]


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").lower() in {"1", "true", "yes"}
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() in {"1", "true", "yes"}
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@supplychain.com"
)

# Email backend - use SMTP for actual sending
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)

# Email timeout to prevent hanging
EMAIL_TIMEOUT = 30

# Blockchain anchoring settings
BLOCKCHAIN_ANCHORING_ENABLED = (
    os.getenv("BLOCKCHAIN_ANCHORING_ENABLED", "false").lower()
    in {"1", "true", "yes"}
)
BLOCKCHAIN_PROVIDER_URL = os.getenv(
    "BLOCKCHAIN_PROVIDER_URL", "http://localhost:8545"
)
BLOCKCHAIN_CONTRACT_ADDRESS = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", None)
BLOCKCHAIN_PRIVATE_KEY = os.getenv("BLOCKCHAIN_PRIVATE_KEY", None)
BLOCKCHAIN_NETWORK_NAME = os.getenv("BLOCKCHAIN_NETWORK_NAME", "ethereum-mainnet")

# =============================================================================
# Structured Logging Configuration (structlog)
# =============================================================================
#
# The application uses structlog for structured logging with the following features:
# - JSON format in production (machine-readable for log aggregation)
# - Pretty console output in development (human-readable)
# - Request/response logging for audit trails
# - Separate log files: app.log, error.log, audit.log
#
# Environment variables:
# - LOG_LEVEL: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# - LOG_JSON: Force JSON output (true/false, defaults based on DEBUG)
# - LOG_TO_FILE: Enable file logging (true/false, defaults to true)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
LOG_JSON = os.getenv("LOG_JSON", "").lower() in {"1", "true", "yes"} if os.getenv("LOG_JSON") else None
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() in {"1", "true", "yes"}
LOG_DIR = BASE_DIR.parent / "logs" if LOG_TO_FILE else None

# Configure structlog at Django startup
from supplychain.logging_config import configure_logging

configure_logging(
    debug=DEBUG,
    log_level=LOG_LEVEL,
    log_dir=LOG_DIR,
    json_logs=LOG_JSON,
)

# API Documentation with drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Supply Chain Tracking API",
    "DESCRIPTION": "A comprehensive API for end-to-end supply chain tracking with blockchain anchoring for tamper-evident provenance",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "CONTACT": {
        "name": "Supply Chain Team",
        "email": "support@supplychain.com",
    },
    "LICENSE": {
        "name": "MIT",
    },
    # Authentication configuration
    "SECURITY": [
        {
            "jwtAuth": [],
        }
    ],
    "COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT authentication using access tokens. Use the `/api/auth/login/` endpoint to obtain tokens.",
            }
        }
    },
    # Swagger UI settings
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
    },
    # Additional settings
    "ENUM_NAME_OVERRIDES": {
        "ValidationErrorEnum": "drf_spectacular.openapi.ValidationErrorEnum.choices",
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}

# =============================================================================
# Caching Configuration (Redis)
# =============================================================================
#
# Redis-based caching for frequently accessed data. Falls back to local memory
# cache if Redis is not configured.
#
# Environment variables:
# - REDIS_URL: Redis connection URL (e.g., redis://localhost:6379/0)
# - CACHE_TIMEOUT: Default cache timeout in seconds (default: 300)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "300"))

try:
    # Try to use Redis if available
    import socket
    host, port = REDIS_URL.replace("redis://", "").split("/")[0].split(":")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, int(port)))
    sock.close()
    redis_available = result == 0
except Exception:
    redis_available = False

if redis_available:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "TIMEOUT": CACHE_TIMEOUT,
            "KEY_PREFIX": "supplychain",
        }
    }
else:
    # Fallback to local memory cache for development
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": CACHE_TIMEOUT,
            "OPTIONS": {
                "MAX_ENTRIES": 1000,
            },
        }
    }

# Session configuration (use cache backend if Redis available)
if redis_available:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# =============================================================================
# File Storage Configuration (MinIO/S3)
# =============================================================================
#
# MinIO-based storage for document management. Uses S3-compatible API.
#
# Environment variables:
# - MINIO_ENDPOINT: MinIO server URL for internal connections (default: http://localhost:9000)
# - MINIO_PUBLIC_ENDPOINT: Public URL for external access (default: same as MINIO_ENDPOINT)
# - MINIO_ACCESS_KEY: Access key (default: minioadmin)
# - MINIO_SECRET_KEY: Secret key (default: minioadmin)
# - MINIO_BUCKET_NAME: Bucket name (default: supplychain-documents)
# - MINIO_USE_SSL: Use SSL (default: false for local dev)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", MINIO_ENDPOINT)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "supplychain-documents")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() in {"1", "true", "yes"}

# django-storages S3 configuration for MinIO
STORAGES = {
    "default": {
        "BACKEND": "supplychain.storage.MinIOStorage",
        "OPTIONS": {
            "access_key": MINIO_ACCESS_KEY,
            "secret_key": MINIO_SECRET_KEY,
            "bucket_name": MINIO_BUCKET_NAME,
            "endpoint_url": MINIO_ENDPOINT,  # Internal endpoint for file operations
            "use_ssl": MINIO_USE_SSL,
            "file_overwrite": False,
            "default_acl": None,
            "querystring_auth": True,  # Generate signed URLs
            "querystring_expire": 3600,  # URL expires in 1 hour
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 50MB default

# Allowed file types for document uploads
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
]

# =============================================================================
# Celery Configuration (RabbitMQ Broker)
# =============================================================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Celery Beat schedule for periodic tasks
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Disable Django fixup to avoid AttributeError with Celery 5.6+ solo pool
# This is a known bug: https://github.com/celery/celery/issues/9aborana
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_FIXUPS = []  # Disable all fixups including the buggy Django fixup

# =============================================================================
# Notification Settings
# =============================================================================
# Event types that trigger immediate notifications
NOTIFICATION_CRITICAL_EVENTS = [
    "recalled",
    "temperature_alert",
    "damaged",
    "expired",
    "error",
]

# Severity levels that trigger notifications
NOTIFICATION_ALERT_SEVERITIES = ["critical", "high"]

# Escalation timeout in minutes (escalate if not acknowledged)
NOTIFICATION_ESCALATION_TIMEOUT = int(os.getenv("NOTIFICATION_ESCALATION_TIMEOUT", "30"))

