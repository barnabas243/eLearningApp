"""
Django settings for eLearningApp project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-kt@57@9xcrs*5=c^-%m99!h!_1cq!!9qx&3!a=1(o=i&$i#b98"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Consolidate similar values
local_hosts = [
    "localhost",
    "127.0.0.1",
    "192.168.10.134",
    "elearningapp-ibrf.onrender.com",
]
trusted_origins = [
    "https://elearningapp-ibrf.onrender.com",
    "http://localhost:8000",
    "https://localhost",
    "https://192.168.10.134",
]

# Set CSRF_TRUSTED_ORIGINS and CORS_ORIGIN_WHITELIST
CSRF_TRUSTED_ORIGINS = trusted_origins
# CORS_ORIGIN_WHITELIST = trusted_origins
CORS_ORIGIN_WHITELIST = trusted_origins
#     "http://" + host + ":8000" for host in local_hosts
# ]

# Set ALLOWED_HOSTS
ALLOWED_HOSTS = local_hosts

# Application definition

INSTALLED_APPS = [
    "daphne",
    "users",
    "elearning_auth",
    "courses",
    "chat",
    "django_htmx",
    "rest_framework",
    "ckeditor",
    "ckeditor_uploader",
    "channels",
    "notifications",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "eLearningApp.urls"

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

WSGI_APPLICATION = "eLearningApp.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

# allow is_active=false users to authenticate. They will not login
# server respond with custom message for such cases
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]
# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Singapore"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# CKEditor configuration
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": [
            ["Format", "Font", "FontSize"],
            ["Bold", "Italic", "Underline", "Strike", "Subscript", "Superscript"],
            [
                "NumberedList",
                "BulletedList",
                "-",
                "Outdent",
                "Indent",
                "-",
                "Blockquote",
            ],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink"],
            ["Image", "Table", "HorizontalRule", "SpecialChar"],
            ["TextColor", "BGColor"],
            ["Source", "Maximize"],
            ["Upload", "Embed", "Iframe"],
        ],
        "height": 300,
        "width": "100%",
        "filebrowserWindowWidth": 800,
        "filebrowserWindowHeight": 500,
        "filebrowserUploadUrl": "/ckeditor/upload/",
        "filebrowserUploadMethod": "xhr",
        "filebrowserBrowseUrl": "/ckeditor/browse/",
        "filebrowserUploadAllowedExtensions": ["pdf", "doc", "docx"],
        "extraPlugins": ",".join(["codesnippet"]),  # Add extra CKEditor plugins
    },
}
# CKEditor Uploader settings
CKEDITOR_UPLOAD_PATH = "uploads/"  # Path where uploaded files will be stored
CKEDITOR_UPLOAD_SLUGIFY_FILENAME = True  # Enable filename slugification
CKEDITOR_ALLOW_NONIMAGE_FILES = True  # Allow uploading non-image files, including PDFs

# Define CKEditor file upload handler URL
CKEDITOR_REST_URL = "/ckeditor/upload/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "awdtest04@gmail.com"
EMAIL_HOST_PASSWORD = "khfm yqfy sagi ociu"  # Google-generated App Password. email password auth is deprecated.

# Celery backend
# CELERY_BROKER_URL = "redis://localhost:6379/0"  # running directly from django
# CELERY_RESULT_BACKEND = "redis://localhost:6379/0"  # running directly from django
# CELERY_BROKER_URL = "redis://redis:6379/0"  # docker redis config
# CELERY_RESULT_BACKEND = "redis://redis:6379/0"  # docker redis config

# daphne
ASGI_APPLICATION = "eLearningApp.asgi.application"

CELERY_BROKER_URL = (
    "redis://red-cnmr84021fec7398jt4g:6379"  # Redis instance name on Render.com
)
CELERY_RESULT_BACKEND = (
    "redis://red-cnmr84021fec7398jt4g:6379"  # Redis instance name on Render.com
)

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                ("red-cnmr84021fec7398jt4g", 6379)
            ],  # Redis instance name on Render.com
        },
    },
}
