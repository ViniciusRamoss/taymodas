"""Settings de produção.

Exige `DJANGO_SECRET_KEY`, `DATABASE_URL`, `CLOUDINARY_URL` e um host (`DJANGO_ALLOWED_HOSTS`
ou `RENDER_EXTERNAL_HOSTNAME`, que o Render define sozinho).
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import STORAGES, env


def require_env(name: str) -> str:
    """Lê uma variável obrigatória; vazia conta como ausente."""
    value: str = env.str(name, default="")
    if not value:
        raise ImproperlyConfigured(f"A variável de ambiente {name} é obrigatória em produção.")
    return value


DEBUG = False
# O Render injeta o próprio host (ex.: taymodas.onrender.com); domínios extras vão em
# DJANGO_ALLOWED_HOSTS. Sem nenhum dos dois, o app não sobe.
ALLOWED_HOSTS = [
    host
    for host in [
        *env.list("DJANGO_ALLOWED_HOSTS", default=[]),
        env.str("RENDER_EXTERNAL_HOSTNAME", default=""),
    ]
    if host
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "A variável de ambiente DJANGO_ALLOWED_HOSTS é obrigatória em produção "
        "(ou RENDER_EXTERNAL_HOSTNAME, definida pelo Render)."
    )

# Disco do servidor gratuito é efêmero: banco e fotos precisam ficar fora dele.
# Falha na inicialização se faltarem, em vez de cair no SQLite / `media/` local.
require_env("DATABASE_URL")
require_env("CLOUDINARY_URL")

STORAGES = {
    **STORAGES,
    "default": {"BACKEND": "apps.core.storage.CloudinaryMediaStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Preload do HSTS é irreversível na prática e não se aplica a subdomínio compartilhado
# (ex.: *.onrender.com). Reavaliar quando houver domínio próprio.
SILENCED_SYSTEM_CHECKS = ["security.W021"]
