"""Páginas Entregas e Como comprar, e os dados da loja que elas mostram."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import StoreSettings

pytestmark = pytest.mark.django_db

DELIVERY_URL = reverse("core:delivery")
HOW_TO_BUY_URL = reverse("core:how_to_buy")


def configure(**fields: str) -> StoreSettings:
    store = StoreSettings.load()
    for name, value in fields.items():
        setattr(store, name, value)
    store.save()
    return store


class TestStoreSettings:
    def test_city_list_ignores_blank_lines(self) -> None:
        store = configure(mototaxi_cities="Serrana\n\n  Cajuru  \n")

        assert store.mototaxi_city_list == ["Serrana", "Cajuru"]

    def test_map_urls_encode_address(self) -> None:
        store = configure(store_address="Rua A, 10, Serrana-SP")

        assert store.map_embed_url == (
            "https://maps.google.com/maps?q=Rua%20A%2C%2010%2C%20Serrana-SP&output=embed"
        )
        assert store.map_link_url.endswith("query=Rua%20A%2C%2010%2C%20Serrana-SP")

    def test_no_address_no_map(self) -> None:
        store = configure(store_address="")

        assert store.map_embed_url == ""
        assert store.map_link_url == ""

    def test_whatsapp_url_needs_number(self) -> None:
        assert configure(whatsapp_number="").whatsapp_url("Oi") is None
        assert (
            configure(whatsapp_number="5516912345678").whatsapp_url("Olá!")
            == "https://wa.me/5516912345678?text=Ol%C3%A1%21"
        )


class TestDeliveryPage:
    def test_shows_cities_map_and_whatsapp(self, client: Client) -> None:
        configure(
            whatsapp_number="5516912345678",
            mototaxi_cities="Serrana\nCajuru",
            store_address="Rua A, 10, Serrana-SP",
        )

        html = client.get(DELIVERY_URL).content.decode()

        assert '<li class="pill">Cajuru</li>' in html
        assert 'src="https://maps.google.com/maps?q=Rua%20A%2C%2010%2C%20Serrana-SP' in html
        assert "https://wa.me/5516912345678?text=" in html
        assert 'aria-current="page"' in html

    def test_without_address_or_number(self, client: Client) -> None:
        configure(whatsapp_number="", store_address="")

        html = client.get(DELIVERY_URL).content.decode()

        assert "<iframe" not in html
        assert "wa.me" not in html

    def test_delivery_details_from_admin(self, client: Client) -> None:
        configure(delivery_info="Envio em até 2 dias úteis.")

        assert "Envio em até 2 dias úteis." in client.get(DELIVERY_URL).content.decode()


class TestHowToBuyPage:
    def test_about_section_only_when_filled(self, client: Client) -> None:
        assert "Sobre a Tay Modas" not in client.get(HOW_TO_BUY_URL).content.decode()

        configure(about_text="Loja de bairro desde sempre.")

        html = client.get(HOW_TO_BUY_URL).content.decode()
        assert "Sobre a Tay Modas" in html
        assert "Loja de bairro desde sempre." in html


def test_pages_in_sitemap(client: Client) -> None:
    xml = client.get("/sitemap.xml").content.decode()

    assert f"http://testserver{DELIVERY_URL}" in xml
    assert f"http://testserver{HOW_TO_BUY_URL}" in xml
