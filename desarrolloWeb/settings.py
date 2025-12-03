"""
Django settings for desarrolloWeb project.
"""

from pathlib import Path
import os
from urllib.parse import urlparse

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================
# SECRET KEY & DEBUG
# ==========================

SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY")
    or os.environ.get("SECRET_KEY")
    or "django-insecure-jt_&bwofr0+hj3h!q1@(hug7)w7x_011lqp7rv^7rqnn+e38=b"
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

# ==========================
# ALLOWED_HOSTS / CSRF
# ==========================

RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_HOSTNAME:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", RENDER_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_HOSTNAME}"]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ==========================
# APPS
# ==========================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inicio",
]

# ==========================
# MIDDLEWARE
# ==========================

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

ROOT_URLCONF = "desarrolloWeb.urls"

# ==========================
# TEMPLATES
# ==========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Usamos templates dentro de las apps (inicio/templates/…)
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

WSGI_APPLICATION = "desarrolloWeb.wsgi.application"

# ==========================
# BASE DE DATOS
# ==========================

# En Render usamos DATABASE_URL (Postgres gestionado).
# En local, si no está DATABASE_URL, se usa la conexión local a Postgres.

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path[1:],  # quita el "/" inicial
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": str(parsed.port or "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "rutek_db",
            "USER": "rutek_admin",
            "PASSWORD": "Rutek123.",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

# ==========================
# PASSWORD VALIDATION
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==========================
# INTERNACIONALIZACIÓN
# ==========================

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"

USE_I18N = True
USE_TZ = True

# ==========================
# ARCHIVOS ESTÁTICOS
# ==========================

STATIC_URL = "/static/"

# En desarrollo: inicio/static
STATICFILES_DIRS = [
    BASE_DIR / "inicio" / "static",
]

# En producción (Render): carpeta donde collectstatic deja los archivos
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================
# CONFIGURACIÓN DE EMAIL
# ==========================

# Usamos siempre SMTP de Gmail para enviar correos reales
# (verificación, recuperación, formulario de contacto, etc.).

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Correo que usará el proyecto para ENVIAR mensajes
# En producción (Render) es mejor definirlos como variables de entorno:
#   EMAIL_HOST_USER = ruteksoporte@gmail.com
#   EMAIL_HOST_PASSWORD = <APP PASSWORD DE GMAIL>
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "ruteksoporte@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "iesokrakwhnqpgjc")

# Remitente por defecto
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

