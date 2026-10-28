from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.test import Client
from django.urls import reverse

from apps.cart.cart import Cart
from apps.cart.services import build_lines, build_whatsapp_cart_url, cart_variants
from apps.catalog.models import ProductVariant
from apps.catalog.tests.factories import (
    ColorFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
)
from apps.core.models import StoreSettings

pytestmark = pytest.mark.django_db

CART_URL = reverse("cart:detail")


def absolute(path: str) -> str:
    return f"https://taymodas.example{path}"


def message_of(url: str) -> str:
    return parse_qs(urlsplit(url).query)["text"][0]


def make_variant(name: str, price: str, size: str, color: str, stock: int = 3) -> ProductVariant:
    return ProductVariantFactory.create(
        product=ProductFactory.create(name=name, price=Decimal(price)),
        size=SizeFactory.create(name=size),
        color=ColorFactory.create(name=color),
        stock=stock,
    )


def fill(client: Client, items: dict[ProductVariant, int]) -> None:
    session = client.session
    session["sacola"] = {str(variant.pk): quantity for variant, quantity in items.items()}
    session.save()


@pytest.fixture
def store() -> StoreSettings:
    settings = StoreSettings.load()
    settings.whatsapp_number = "5511900000000"
    settings.save()
    return settings


class TestCart:
    def test_add_set_remove_and_count(self) -> None:
        cart = Cart(SessionStore())

        cart.add(1, stock=5)
        cart.add(1, stock=5)
        cart.add(2, stock=1)
        cart.add(2, stock=1)

        assert cart.items == {1: 2, 2: 1}
        assert cart.count == 3

        cart.set(1, 9, stock=4)
        assert cart.items[1] == 4

        cart.set(1, 0, stock=4)
        cart.remove(2)
        assert cart.items == {}

    def test_clear_empties_the_session(self) -> None:
        session = SessionStore()
        cart = Cart(session)
        cart.add(1, stock=1)

        cart.clear()

        assert "sacola" not in session
        assert cart.count == 0


class TestBuildWhatsappCartUrl:
    def test_lists_every_piece_and_the_total(self) -> None:
        dress = make_variant("Vestido Midi", "189.9", "M", "Preto")
        top = make_variant("Blusa Farm", "50", "P", "Estampada")
        items = {dress.pk: 2, top.pk: 1}
        store = StoreSettings(whatsapp_number="5511900000000")

        url = build_whatsapp_cart_url(build_lines(items, cart_variants(items)), store, absolute)

        assert url is not None
        assert url.startswith("https://wa.me/5511900000000?text=")
        assert message_of(url) == (
            "Olá! Quero fazer este pedido:\n\n"
            "• 2x Vestido Midi (Preto, tam. M): R$ 379,80\n"
            f"{absolute(dress.product.get_absolute_url())}\n\n"
            "• 1x Blusa Farm (Estampada, tam. P): R$ 50,00\n"
            f"{absolute(top.product.get_absolute_url())}\n\n"
            "Total: R$ 429,80"
        )

    def test_sold_out_pieces_stay_out(self) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        gone = make_variant("Body Renda", "60", "P", "Branco", stock=0)
        items = {dress.pk: 1, gone.pk: 1}

        lines = build_lines(items, cart_variants(items))
        url = build_whatsapp_cart_url(
            lines, StoreSettings(whatsapp_number="5511900000000"), absolute
        )

        assert [line.is_available for line in lines] == [True, False]
        assert url is not None
        assert "Body Renda" not in message_of(url)
        assert message_of(url).endswith("Total: R$ 100,00")

    @pytest.mark.parametrize("template", ["Quero {", "Quero {}", "{itens.x}", "{produto}"])
    def test_broken_message_falls_back_to_default(self, template: str) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        items = {dress.pk: 1}
        store = StoreSettings(whatsapp_number="5511900000000", order_message_template=template)

        url = build_whatsapp_cart_url(build_lines(items, cart_variants(items)), store, absolute)

        assert url is not None
        assert message_of(url).startswith("Olá! Quero fazer este pedido:")

    def test_custom_message(self) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        items = {dress.pk: 1}
        store = StoreSettings(
            whatsapp_number="5511900000000", order_message_template="Oi! Total {total}"
        )

        url = build_whatsapp_cart_url(build_lines(items, cart_variants(items)), store, absolute)

        assert url is not None
        assert message_of(url) == "Oi! Total R$ 100,00"

    def test_no_url_without_number_or_available_pieces(self) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        gone = make_variant("Body Renda", "60", "P", "Branco", stock=0)
        lines = build_lines({dress.pk: 1}, cart_variants([dress.pk]))
        sold_out = build_lines({gone.pk: 1}, cart_variants([gone.pk]))

        assert build_whatsapp_cart_url(lines, StoreSettings(), absolute) is None
        store = StoreSettings(whatsapp_number="5511900000000")
        assert build_whatsapp_cart_url(sold_out, store, absolute) is None


class TestCartPage:
    def test_empty_bag(self, client: Client, store: StoreSettings) -> None:
        response = client.get(CART_URL)

        content = response.content.decode()
        assert response.status_code == 200
        assert "Sua sacola está vazia." in content
        assert '<meta name="robots" content="noindex">' in content
        assert "wa.me" not in content

    def test_lists_pieces_total_and_whatsapp_link(
        self, client: Client, store: StoreSettings
    ) -> None:
        dress = make_variant("Vestido Midi", "189.9", "M", "Preto")
        top = make_variant("Blusa Farm", "50", "P", "Estampada")
        fill(client, {dress: 2, top: 1})

        content = client.get(CART_URL).content.decode()

        assert "Vestido Midi" in content and "Blusa Farm" in content
        assert "Cor Preto, tamanho M" in content
        assert "R$ 379,80" in content
        assert "R$ 429,80" in content
        assert "https://wa.me/5511900000000?text=" in content
        assert 'aria-current="page"' in content

    def test_hidden_product_and_unknown_ids_are_dropped(
        self, client: Client, store: StoreSettings
    ) -> None:
        hidden = make_variant("Peça Oculta", "80", "M", "Preto")
        hidden.product.is_active = False
        hidden.product.save()
        session = client.session
        session["sacola"] = {str(hidden.pk): 1, "999999": 2}
        session.save()

        content = client.get(CART_URL).content.decode()

        assert "Peça Oculta" not in content
        assert "Sua sacola está vazia." in content

    def test_sold_out_piece_is_flagged(self, client: Client, store: StoreSettings) -> None:
        gone = make_variant("Body Renda", "60", "P", "Branco", stock=0)
        fill(client, {gone: 1})

        content = client.get(CART_URL).content.decode()

        assert "Esgotou" in content
        assert "As peças que esgotaram ficam fora do pedido." in content
        assert "wa.me" not in content
        # Aparece uma vez; depois sai da sacola e do contador.
        assert client.session["sacola"] == {}

    def test_update_quantity_caps_at_stock(self, client: Client, store: StoreSettings) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto", stock=2)
        fill(client, {dress: 1})

        response = client.post(reverse("cart:update", args=[dress.pk]), {"quantidade": "5"})

        assert response.status_code == 302
        assert response["Location"] == CART_URL
        assert client.session["sacola"] == {str(dress.pk): 2}

    @pytest.mark.parametrize("quantity", ["0", "", "abc"])
    def test_zero_or_invalid_quantity_removes(
        self, client: Client, store: StoreSettings, quantity: str
    ) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        fill(client, {dress: 1})

        client.post(reverse("cart:update", args=[dress.pk]), {"quantidade": quantity})

        assert client.session["sacola"] == {}

    def test_update_unknown_variant_is_404(self, client: Client) -> None:
        response = client.post(reverse("cart:update", args=[999999]), {"quantidade": "1"})

        assert response.status_code == 404

    def test_clear(self, client: Client, store: StoreSettings) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        fill(client, {dress: 1})

        response = client.post(reverse("cart:clear"))

        assert response.status_code == 302
        assert "sacola" not in client.session

    def test_changes_need_post(self, client: Client) -> None:
        assert client.get(reverse("cart:clear")).status_code == 405
        assert client.get(reverse("cart:update", args=[1])).status_code == 405

    def test_header_counts_pieces(self, client: Client, store: StoreSettings) -> None:
        dress = make_variant("Vestido Midi", "100", "M", "Preto")
        fill(client, {dress: 2})

        content = client.get(reverse("core:how_to_buy")).content.decode()

        assert f'href="{CART_URL}"' in content
        assert '2<span class="sr-only"> peças</span>' in content


def test_robots_keeps_bag_out(client: Client) -> None:
    assert "Disallow: /sacola/" in client.get("/robots.txt").content.decode()
