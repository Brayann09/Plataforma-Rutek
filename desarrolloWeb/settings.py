"""
Django settings for desarrolloWeb project.
"""

from pathlib import Path
import os
from urllib.parse import urlparse

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# 🔐 SECRET KEY & DEBUG
# ==============================

# En producción (Render) se debe definir DJANGO_SECRET_KEY (o SECRET_KEY).
# En local, si no hay variable, usa la que ya tenías.
SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY")
    or os.environ.get("SECRET_KEY")
    or "django-insecure-jt_&bwofr0+hj3h!q1@(hug7)w7x_011lqp7rv^7rqnn+e38=b"
)

# DEBUG: en Render pondremos DEBUG=False, en local normalmente True
DEBUG = os.environ.get("DEBUG", "True") == "True"

# ==============================
# 🌍 ALLOWED_HOSTS / CSRF
# ==============================

# Render expone el host en RENDER_EXTERNAL_HOSTNAME
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_HOSTNAME:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", RENDER_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_HOSTNAME}"]
else:
    # Localhost por defecto
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# ==============================
#  APPS
# ==============================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inicio',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ sirve estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'desarrolloWeb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Usamos templates dentro de apps (inicio/templates/...)
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'desarrolloWeb.wsgi.application'


# ==============================
#  🔵 BASE DE DATOS
# ==============================
# En Render usaremos DATABASE_URL (Postgres gestionado).
# En local, si no está DATABASE_URL, se usa tu configuración actual.

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Ejemplo de DATABASE_URL:
    # postgres://usuario:password@host:puerto/nombre_bd
    parsed = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path[1:],  # quitar el primer '/'
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": str(parsed.port or "5432"),
        }
    }
else:
    # Config LOCAL (tal como la tenías)
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


# ==============================
#  PASSWORD VALIDATION
# ==============================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==============================
#  INTERNACIONALIZACIÓN
# ==============================

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'

USE_I18N = True
USE_TZ = True


# ==============================
#  ARCHIVOS ESTÁTICOS
# ==============================

# URL pública de los estáticos
STATIC_URL = "/static/"

# En desarrollo sigues usando inicio/static
STATICFILES_DIRS = [
    BASE_DIR / "inicio" / "static",
]

# En producción (Render) collectstatic va a dejar todo aquí
STATIC_ROOT = BASE_DIR / "staticfiles"

# Storage optimizado para producción (solo cuando NO estás en DEBUG)
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ==============================
#  DEFAULT AUTO FIELD
# ==============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================
#  📧 CONFIGURACIÓN DE EMAIL
# ==============================
# Por defecto usaremos Gmail (para desarrollo/local),
# pero si la variable EMAIL_BACKEND == "sendgrid",
# usaremos la integración con SendGrid.

EMAIL_BACKEND_ENV = os.environ.get("EMAIL_BACKEND", "").lower()

if EMAIL_BACKEND_ENV == "sendgrid":
    # ------ PRODUCCIÓN (Render) con SendGrid ------
    EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")

    # Remitente por defecto (debe estar verificado en SendGrid)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "no-reply@rutek.com")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

    # Opcionales para controlar la entrega
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
    SENDGRID_ECHO_TO_STDOUT = False

else:
    # ------ DESARROLLO / LOCALHOST con Gmail ------
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True

    # Tu Gmail y contraseña de aplicación SOLO en local (.env)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "ruteksoporte@gmail.com")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "iesokrakwhnqpgjc")

    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
