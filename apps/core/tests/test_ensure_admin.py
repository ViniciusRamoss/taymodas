import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_creates_superuser_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_ADMIN_USERNAME", "tay")
    monkeypatch.setenv("DJANGO_ADMIN_PASSWORD", "uma-senha-longa-123")

    call_command("ensure_admin", stdout=None)
    call_command("ensure_admin", stdout=None)

    user = get_user_model().objects.get()
    assert user.is_superuser
    assert user.check_password("uma-senha-longa-123")


def test_does_nothing_without_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_ADMIN_PASSWORD", raising=False)

    call_command("ensure_admin", stdout=None)

    assert not get_user_model().objects.exists()
