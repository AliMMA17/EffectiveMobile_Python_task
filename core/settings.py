"""
Django settings for core project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Base path
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local env vars (doesn't override real env, e.g. in Docker)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# --- Core config from env ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
DEBUG = bool(int(os.getenv("DEBUG", "1")))
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",")]

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts",
    "accesscontrol",
    "authn",
    "mockbiz",
]

# --- Middleware (CORS before CommonMiddleware; our JWT last) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",    # <-- keep before CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # keep for admin
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authn.middleware.JWTAuthMiddleware",       # <-- our custom identification
]

ROOT_URLCONF = "core.urls"

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

WSGI_APPLICATION = "core.wsgi.application"

# --- Database (switch via USE_SQLITE=1/0) ---
USE_SQLITE = bool(int(os.getenv("USE_SQLITE", "1")))
if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "app"),
            "USER": os.getenv("DB_USER", "app"),
            "PASSWORD": os.getenv("DB_PASSWORD", "app"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

# --- Auth / DRF ---
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "authn.drf_auth.JWTHeaderAuthentication",
    ],
    "UNAUTHENTICATED_USER": None,
}

# Store passwords with bcrypt (as per task hint)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # fallback
]

# --- i18n / tz ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Misc ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS (open for testing; tighten later) ---
CORS_ALLOW_ALL_ORIGINS = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "authn.middleware": {  # our middleware logger
            "handlers": ["console"],
            "level": "INFO",    # change to "DEBUG" for more noise
            "propagate": False,
        },
    },
}


REFRESH_TOKEN_BYTES = int(os.getenv("REFRESH_TOKEN_BYTES", "32"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))