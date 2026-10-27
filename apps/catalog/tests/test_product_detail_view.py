import re
from urllib.parse import unquote

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.catalog.models import Product, ProductVariant
from apps.core.models import StoreSettings

from .factories import (
    CategoryFactory,
    ColorFactory,
    ProductFactory,
    ProductImageFactory,
    ProductVariantFactory,
    SizeFactory,
)

pytestmark = pytest.mark.django_db

HTMX = {"HX-Request": "true"}


@pytest.fixture
def store() -> StoreSettings:
    settings = StoreSettings.load()
    settings.whatsapp_number = "5511900000000"
    settings.save()
    return settings


@pytest.fixture
def product() -> Product:
    """Vestido em P/Preto e M/Preto (com estoque) e M/Vinho (esgotado)."""
    dress = ProductFactory.create(
        name="Vestido Midi", category=CategoryFactory.create(name="Vestidos")
    )
    small, medium = SizeFactory.create(name="P"), SizeFactory.create(name="M")
    black, wine = ColorFactory.create(name="Preto"), ColorFactory.create(name="Vinho")
    ProductVariantFactory.create(product=dress, size=small, color=black)
    ProductVariantFactory.create(product=dress, size=medium, color=black)
    ProductVariantFactory.create(product=dress, size=medium, color=wine, stock=0)
    return dress


def variant(product: Product, size: str, color: str) -> ProductVariant:
    return product.variants.get(size__name=size, color__name=color)


def choose(product: Product, size: str, color: str) -> dict[str, int]:
    chosen = variant(product, size, color)
    return {"tamanho": chosen.size.pk, "cor": chosen.color.pk}


class TestProductDetailView:
    def test_shows_product_without_order_button_until_choice(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        ProductImageFactory.create(product=product, alt_text="Vestido de frente")

        response = client.get(product.get_absolute_url())

        content = response.content.decode()
        assert response.status_code == 200
        assert "<h1" in content and "Vestido Midi" in content
        assert "Vestido de frente" in content
        assert "?categoria=vestidos" in content
        assert "Escolha a cor e o tamanho para fazer o pedido." in content
        assert "wa.me" not in content

    def test_full_choice_shows_whatsapp_link(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.get(product.get_absolute_url(), choose(product, "M", "Preto"))

        content = unquote(response.content.decode())
        assert "https://wa.me/5511900000000?text=" in content
        assert "Tamanho: M" in content
        assert f"http://testserver{product.get_absolute_url()}" in content

    def test_sold_out_combination_explains_and_hides_button(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        content = client.get(
            product.get_absolute_url(), choose(product, "M", "Vinho")
        ).content.decode()

        assert "M na cor Vinho esgotou." in content
        assert "wa.me" not in content

    def test_without_store_number_hides_button(self, client: Client, product: Product) -> None:
        content = client.get(
            product.get_absolute_url(), choose(product, "M", "Preto")
        ).content.decode()

        assert "wa.me" not in content
        assert "Pedir pelo WhatsApp" not in content

    def test_htmx_request_returns_only_the_form(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.get(
            product.get_absolute_url(), choose(product, "P", "Preto"), headers=HTMX
        )

        content = response.content.decode()
        assert 'id="pedido"' in content
        assert "<html" not in content
        assert "Pedir pelo WhatsApp" in content
        assert "HX-Request" in response["Vary"]

    def test_htmx_history_restore_gets_full_page(self, client: Client, product: Product) -> None:
        response = client.get(
            product.get_absolute_url(), headers={**HTMX, "HX-History-Restore-Request": "true"}
        )

        assert "<html" in response.content.decode()

    def test_invalid_params_are_ignored(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.get(product.get_absolute_url(), {"tamanho": "abc", "cor": "-1"})

        assert response.status_code == 200
        assert "Escolha a cor e o tamanho" in response.content.decode()

    def test_order_button_is_visible_before_choice(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        content = client.get(product.get_absolute_url()).content.decode()

        assert 'name="pedir" value="1"' in content
        assert "autofocus" not in content

    def test_order_without_full_choice_points_to_missing_group(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        black = variant(product, "P", "Preto").color
        params: dict[str, int | str] = {"cor": black.pk, "pedir": "1"}

        response = client.get(product.get_absolute_url(), params, headers=HTMX)

        content = response.content.decode()
        small = variant(product, "P", "Preto").size
        assert "escolha um" in content
        assert re.search(f'id="tamanho-{small.pk}"[^>]*autofocus', content)
        assert content.count("autofocus") == 1
        assert "font-medium text-tinta" in content

    def test_order_with_full_choice_without_js_redirects_to_whatsapp(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        params: dict[str, int | str] = {**choose(product, "M", "Preto"), "pedir": "1"}

        response = client.get(product.get_absolute_url(), params)

        assert response.status_code == 302
        assert response["Location"].startswith("https://wa.me/5511900000000?text=")

    def test_sold_out_product_shows_message_instead_of_form(self, client: Client) -> None:
        sold_out = ProductFactory.create()
        ProductVariantFactory.create(product=sold_out, stock=0)

        content = client.get(sold_out.get_absolute_url()).content.decode()

        assert "Esta peça esgotou." in content
        assert 'id="pedido"' not in content

    @pytest.mark.parametrize(("product_active", "category_active"), [(False, True), (True, False)])
    def test_hidden_product_is_404(
        self, client: Client, product_active: bool, category_active: bool
    ) -> None:
        product = ProductFactory.create(
            is_active=product_active,
            category=CategoryFactory.create(name="Oculta", is_active=category_active),
        )

        assert client.get(product.get_absolute_url()).status_code == 404

    def test_query_count_does_not_grow_with_variants_or_photos(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        def count_queries() -> int:
            with CaptureQueriesContext(connection) as ctx:
                client.get(product.get_absolute_url(), choose(product, "P", "Preto"))
            return len(ctx.captured_queries)

        baseline = count_queries()
        for _ in range(3):
            ProductImageFactory.create(product=product)
            ProductVariantFactory.create(product=product)

        assert count_queries() == baseline


def test_list_cards_link_to_detail(client: Client) -> None:
    product = ProductFactory.create()

    content = client.get(reverse("catalog:product_list")).content.decode()

    assert f'href="{product.get_absolute_url()}"' in content
