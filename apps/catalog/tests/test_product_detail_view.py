import re

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
        assert "Escolha a cor e o tamanho para adicionar à sacola." in content

    def test_full_choice_is_ready_for_the_bag(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.get(product.get_absolute_url(), choose(product, "M", "Preto"))

        content = response.content.decode()
        assert "Adicionar à sacola" in content
        assert "Junte quantas peças quiser" in content

    def test_sold_out_combination_explains_and_hides_button(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        content = client.get(
            product.get_absolute_url(), choose(product, "M", "Vinho")
        ).content.decode()

        assert "M na cor Vinho esgotou." in content

    def test_without_store_number_hides_button(self, client: Client, product: Product) -> None:
        content = client.get(
            product.get_absolute_url(), choose(product, "M", "Preto")
        ).content.decode()

        assert "Adicionar à sacola" not in content
        assert 'id="contador-sacola"' not in content

    def test_htmx_request_returns_only_the_form(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.get(
            product.get_absolute_url(), choose(product, "P", "Preto"), headers=HTMX
        )

        content = response.content.decode()
        assert 'id="pedido"' in content
        assert "<html" not in content
        assert "Adicionar à sacola" in content
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

        assert f'hx-post="{product.get_absolute_url()}"' in content
        assert "autofocus" not in content

    def test_order_without_full_choice_points_to_missing_group(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        black = variant(product, "P", "Preto").color
        response = client.post(product.get_absolute_url(), {"cor": black.pk}, headers=HTMX)

        content = response.content.decode()
        small = variant(product, "P", "Preto").size
        assert "escolha um" in content
        assert re.search(f'id="tamanho-{small.pk}"[^>]*autofocus', content)
        assert content.count("autofocus") == 1
        assert "font-medium text-tinta" in content

    def test_add_without_choice_points_to_color_first(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        content = client.post(product.get_absolute_url(), {}, headers=HTMX).content.decode()

        black = variant(product, "P", "Preto").color
        assert "escolha uma" in content
        assert re.search(f'id="cor-{black.pk}"[^>]*autofocus', content)

    def test_add_without_js_redirects_back_with_notice(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        chosen = choose(product, "M", "Preto")

        response = client.post(product.get_absolute_url(), chosen)

        assert response.status_code == 302
        assert "adicionado=1" in response["Location"]
        assert client.session["sacola"] == {str(variant(product, "M", "Preto").pk): 1}
        page = client.get(response["Location"]).content.decode()
        assert "Peça na sacola." in page
        assert re.search(r'id="contador-sacola".*?>1<', page, re.S)

    def test_add_with_htmx_returns_form_and_counter(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.post(
            product.get_absolute_url(), choose(product, "P", "Preto"), headers=HTMX
        )

        content = response.content.decode()
        assert response.status_code == 200
        assert "<html" not in content
        assert "Peça na sacola." in content
        assert 'id="contador-sacola"' in content and 'hx-swap-oob="true"' in content

    def test_add_never_goes_over_stock(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        for _ in range(3):
            client.post(product.get_absolute_url(), choose(product, "P", "Preto"))

        assert client.session["sacola"] == {str(variant(product, "P", "Preto").pk): 1}

    def test_add_sold_out_combination_adds_nothing(
        self, client: Client, product: Product, store: StoreSettings
    ) -> None:
        response = client.post(product.get_absolute_url(), choose(product, "M", "Vinho"))

        assert response.status_code == 200
        assert "M na cor Vinho esgotou." in response.content.decode()
        assert "sacola" not in client.session

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
