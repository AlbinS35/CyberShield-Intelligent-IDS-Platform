"""
CyberShield Core Django Settings
PostgreSQL, Redis, JWT, CORS, Channels, Celery, and RBAC configuration.
Uses python-decouple for type-safe environment variable loading.
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY", default="CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR")
DEBUG = config("DEBUG", default=True, cast=bool)

# Accept ALLOWED_HOSTS as either space-separated or comma-separated in .env
_raw_hosts = config("ALLOWED_HOSTS", default="localhost 127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.replace(",", " ").split() if h.strip()]
# Always include Docker service hostname so the suricata-watcher container
# can POST to http://backend:8000/ without a DisallowedHost rejection.
for _h in ["backend", "cybershield_backend", ".localhost", "testserver"]:
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)


# ─── Applications ─────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "channels",
    "django_celery_beat",
    "drf_spectacular",
]

LOCAL_APPS = [
    "authentication",
    "ingestion",
    "detection",
    "forensics",
    "core",           # Normalized tbl_ schema: 7 canonical IDS models
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",      # Serve static files efficiently
    "corsheaders.middleware.CorsMiddleware",          # Must be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cybershield_core.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "cybershield_core.urls"

TEMPLATES = [
    {
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
    },
]

# ─── ASGI / Django Channels ───────────────────────────────────────────────────
ASGI_APPLICATION = "cybershield_core.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ─── Database — PostgreSQL / TiDB support ─────────────────────────────────────
DB_ENGINE_CHOICE = config("DB_ENGINE", default="postgresql")
if DB_ENGINE_CHOICE == "mysql":
    import pymysql
    pymysql.install_as_MySQLdb()
    DB_ENGINE = "django.db.backends.mysql"
else:
    DB_ENGINE = "django.db.backends.postgresql"

DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": config("DB_NAME", default="cybershield_db"),
        "USER": config("DB_USER", default="cybershield_user"),
        "PASSWORD": config("DB_PASSWORD", default="cybershield_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

if DB_ENGINE == "django.db.backends.mysql":
    DATABASES["default"]["OPTIONS"] = {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "connect_timeout": 10,
    }

# ─── Cache Backend ────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cybershield-cache",
    }
}

# ─── Custom User Model ────────────────────────────────────────────────────────
AUTH_USER_MODEL = "authentication.User"

# ─── Authentication Backends ──────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",       # Standard Django auth
]

# ─── Password Hashing ─────────────────────────────────────────────────────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# ─── Password Validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ─── REST Framework + JWT ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authentication.authenticate.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login_attempts": "5/minute",
        # Public registration rate-limit: prevents automated tenant flooding
        # and bulk account-generation attacks (10 registrations per IP per hour).
        "registration": "10/hour",
    }
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_REFRESH_SERIALIZER": "authentication.serializers.CyberShieldTokenRefreshSerializer",
}

# ─── CORS Configuration ───────────────────────────────────────────────────────
# Allow React/Vite frontend locally and on Render (read FRONTEND_URL from env)
_frontend_url = config("FRONTEND_URL", default="")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server (primary React frontend)
    "http://localhost:5174",   # Vite fallback port
    "http://localhost:3000",   # Create-React-App fallback
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
if _frontend_url:
    CORS_ALLOWED_ORIGINS.append(_frontend_url)

_csrf_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
if _frontend_url:
    _csrf_origins.append(_frontend_url)
CSRF_TRUSTED_ORIGINS = _csrf_origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ─── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─── OpenAPI / Swagger ────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "CyberShield API",
    "DESCRIPTION": (
        "Intelligent Intrusion Detection, Prevention, and Digital Forensics Platform. "
        "Includes normalized tbl_ schema endpoints for telemetry ingestion, asset "
        "management, forensic case vault, and automated containment playbooks."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Production Security (enabled when DEBUG=False) ───────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = False   # Render handles SSL termination upstream
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ─── Default primary key ─────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Email Configuration for Password Reset
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@cybershield.demo'
