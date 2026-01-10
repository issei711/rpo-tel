from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTANCE_CONNECTION_NAME = os.environ.get("CLOUDSQL_INSTANCE_CONNECTION_NAME")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": f"/cloudsql/{INSTANCE_CONNECTION_NAME}",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        # 500のスタックトレースはここに出る
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        # DB/ORM系の例外調査に便利（うるさければ後でOFF）
        "django.db.backends": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        # セキュリティ/CSRF系
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
