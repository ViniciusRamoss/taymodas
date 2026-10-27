import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_healthcheck_returns_ok(client: Client) -> None:
    response = client.get(reverse("core:healthcheck"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_healthcheck_rejects_post(client: Client) -> None:
    response = client.post(reverse("core:healthcheck"))

    assert response.status_code == 405


def test_admin_url_requires_login(client: Client) -> None:
    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/login/" in response["Location"]
