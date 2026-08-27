"""
Test settings for RentSecureBE E2E testing.

Uses a dedicated SQLite test database (or PostgreSQL if configured via
DATABASE_URL / DB_ENGINE).

Never use this settings file in production.
"""

from decouple import config

from .settings import *  # noqa: F403
from .settings import BASE_DIR

DEBUG = True
DJANGO_ENV = "test"
ENVIRONMENT = "test"

SECRET_KEY = "test-secret-key-rentsecure-e2e-2026-abcdefghijklmnopqrstuvwxyz"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_e2e_test.sqlite3",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "e2e-test-cache",
        "TIMEOUT": 300,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://127.0.0.1:6379/1")],
        },
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

USE_SQLITE = True
