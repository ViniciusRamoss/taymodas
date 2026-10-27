import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

REQUIRED = {
    "DJANGO_SECRET_KEY": "test-secret",
    "DJANGO_ALLOWED_HOSTS": "taymodas.example.com,www.taymodas.example.com",
    "DATABASE_URL": "postgres://u:p@db.example.com:5432/taymodas",
    "CLOUDINARY_URL": "cloudinary://key:secret@cloud",
}


def load_prod_settings(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> object:
    for name, value in {**REQUIRED, **overrides}.items():
        monkeypatch.setenv(name, value)
    sys.modules.pop("config.settings.prod", None)
    return importlib.import_module("config.settings.prod")


def test_prod_uses_cloudinary_and_secure_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    prod = load_prod_settings(monkeypatch)

    assert prod.DEBUG is False  # type: ignore[attr-defined]
    assert prod.ALLOWED_HOSTS == [  # type: ignore[attr-defined]
        "taymodas.example.com",
        "www.taymodas.example.com",
    ]
    assert prod.STORAGES["default"]["BACKEND"] == (  # type: ignore[attr-defined]
        "apps.core.storage.CloudinaryMediaStorage"
    )
    assert prod.SESSION_COOKIE_SECURE is True  # type: ignore[attr-defined]


@pytest.mark.parametrize("name", ["DATABASE_URL", "CLOUDINARY_URL", "DJANGO_ALLOWED_HOSTS"])
def test_prod_refuses_to_start_with_empty_required_variable(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    with pytest.raises(ImproperlyConfigured, match=name):
        load_prod_settings(monkeypatch, **{name: ""})
