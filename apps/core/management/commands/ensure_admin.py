"""Cria o usuário administrador a partir de variáveis de ambiente, se ainda não existir.

O Render free não tem shell, então `createsuperuser` interativo não é opção. Roda a cada
deploy; não altera um usuário que já existe (a senha é trocada pelo próprio admin).
"""

from typing import Any

import environ
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

env = environ.Env()


class Command(BaseCommand):
    help = "Cria o superusuário de DJANGO_ADMIN_USERNAME/EMAIL/PASSWORD, se não existir."

    def handle(self, *args: Any, **options: Any) -> None:
        username = env.str("DJANGO_ADMIN_USERNAME", default="")
        password = env.str("DJANGO_ADMIN_PASSWORD", default="")
        if not username or not password:
            self.stdout.write("ensure_admin: variáveis não definidas, nada a fazer.")
            return

        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"ensure_admin: usuário {username!r} já existe.")
            return

        user_model.objects.create_superuser(
            username=username,
            email=env.str("DJANGO_ADMIN_EMAIL", default=""),
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"ensure_admin: usuário {username!r} criado."))
