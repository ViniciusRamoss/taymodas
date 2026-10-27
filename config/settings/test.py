"""Settings usados pelo pytest: rápidos, isolados e sem depender de `.env`."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-secret")

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["testserver"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# Evita o aviso do WhiteNoise sobre STATIC_ROOT inexistente (não rodamos collectstatic nos testes).
WHITENOISE_AUTOREFRESH = True
