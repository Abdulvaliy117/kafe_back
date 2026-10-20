"""
Django settings for osman_cafe project.

Осман Кафе (Ош) — сайт-меню с заказом через WhatsApp.

Конфигурация на .env (python-decouple + python-dotenv):
    SECRET_KEY, DEBUG, ALLOWED_HOSTS, CORS_*, WHATSAPP_NUMBER, ...
"""

import os
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))


# Quick-start development settings - unsuitable for production

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-only-change-me")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Для входа в /admin/ по https за nginx на сервере.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_yasg',
    'corsheaders',
    'apps.catalog',
    'apps.orders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_links',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database — DATABASE_URL из окружения (Supabase/Render Postgres),
# локально без переменной — sqlite.

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# DRF: чтение меню — всем, запись — персоналу; заявки — с троттлингом.

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Оформление заказа: не более 10 попыток в минуту с IP.
        'orders': '10/min',
    },
}


# CORS: витрина Next.js живёт на другом origin.
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=DEBUG, cast=bool)
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://.*\.vercel\.app$"]


# Номер WhatsApp для wa.me-ссылок (только цифры). В /admin/ можно переопределить
# через «Контакты сайта» (SiteInfo).
WHATSAPP_NUMBER = config("WHATSAPP_NUMBER", default="99670000000")

# Цена доставки по городу (сом) — значение по умолчанию для SiteInfo.
DELIVERY_FEE = config("DELIVERY_FEE", default="100")

# Адрес сайта-витрины (Next.js). Используется для кнопок «Открыть сайт» и
# «Пульт менеджера» в шапке админки.
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000").rstrip("/")


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Хранилища: статика — whitenoise, медиа — локально по умолчанию.
# На проде медиа переключается на Supabase Storage (S3), если заданы SUPABASE_S3_*.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Фото блюд и логотип грузятся из /admin/
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Supabase Storage (S3-совместимый) для фото блюд ---
# Нужен на Render/VPS: локальный диск там эфемерный, фото пропадут при передеплое.
# В Supabase: Storage -> создайте публичный bucket, затем Project Settings -> S3.
SUPABASE_S3_BUCKET = config("SUPABASE_S3_BUCKET", default="")
if SUPABASE_S3_BUCKET:
    _s3_public = (config("SUPABASE_S3_PUBLIC_URL", default="")
                  .replace("https://", "").replace("http://", "").strip("/"))
    _s3_options = {
        "access_key": config("SUPABASE_S3_ACCESS_KEY"),
        "secret_key": config("SUPABASE_S3_SECRET_KEY"),
        "bucket_name": SUPABASE_S3_BUCKET,
        "region_name": config("SUPABASE_S3_REGION", default="us-east-1"),
        "endpoint_url": config("SUPABASE_S3_ENDPOINT"),
        # Supabase S3 работает только в path-style, ACL не поддерживается.
        "addressing_style": "path",
        "default_acl": None,
        "querystring_auth": False,
        "file_overwrite": False,
    }
    if _s3_public:
        _s3_options["custom_domain"] = _s3_public
        MEDIA_URL = f"https://{_s3_public}/"
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": _s3_options,
    }
