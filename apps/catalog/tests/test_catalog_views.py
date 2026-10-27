from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import CommandError, call_command
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.catalog import selectors
from apps.catalog.models import Product
from apps.catalog.presenters import NEW_PRODUCT_DAYS, ProductCard

from .factories import (
    CategoryFactory,
    ColorFactory,
    ProductFactory,
    ProductImageFactory,
    ProductVariantFactory,
    SizeFactory,
)

pytestmark = pytest.mark.django_db

URL = reverse("catalog:product_list")


def card_for(product: Product) -> ProductCard:
    return ProductCard.from_product(selectors.catalog_products().get(pk=product.pk))


class TestSelectors:
    def test_available_products_come_before_sold_out(self) -> None:
        sold_out = ProductFactory.create()
        older_available = ProductFactory.create()
        ProductVariantFactory.create(product=older_available, stock=1)
        newer_available = ProductFactory.create()
        ProductVariantFactory.create(product=newer_available, stock=1)

        assert list(selectors.catalog_products()) == [newer_available, older_available, sold_out]

    def test_filters_by_category_and_hides_inactive(self) -> None:
        dresses = CategoryFactory.create(name="Vestidos")
        dress = ProductFactory.create(category=dresses)
        ProductFactory.create(category=dresses, is_active=False)
        ProductFactory.create()

        assert list(selectors.catalog_products(category=dresses)) == [dress]

    def test_categories_with_products_skips_empty_and_inactive(self) -> None:
        with_products = ProductFactory.create().category
        CategoryFactory.create(name="Vazia")
        ProductFactory.create(category=CategoryFactory.create(name="Oculta", is_active=False))
        ProductFactory.create(category=CategoryFactory.create(name="Só inativos"), is_active=False)

        assert list(selectors.categories_with_products()) == [with_products]


class TestProductCard:
    def test_lists_only_sizes_and_colors_in_stock_in_order(self) -> None:
        product = ProductFactory.create(price=Decimal("1299.9"))
        small, large = (
            SizeFactory.create(name="P", position=1),
            SizeFactory.create(name="G", position=3),
        )
        black, wine = (
            ColorFactory.create(name="Preto"),
            ColorFactory.create(name="Vinho", hex_code=""),
        )
        ProductVariantFactory.create(product=product, size=large, color=wine, stock=1)
        ProductVariantFactory.create(product=product, size=small, color=black, stock=2)
        ProductVariantFactory.create(
            product=product, size=SizeFactory.create(name="GG", position=4), color=black, stock=0
        )

        card = card_for(product)

        assert card.price == "R$ 1.299,90"
        assert card.sizes == ("P", "G")
        assert [c.name for c in card.colors] == ["Preto", "Vinho"]
        assert card.colors[1].hex_code == ""
        assert card.is_sold_out is False

    def test_product_without_stock_is_sold_out_and_not_new(self) -> None:
        card = card_for(ProductFactory.create())

        assert card.is_sold_out is True
        assert card.is_new is False
        assert card.sizes == ()

    @pytest.mark.parametrize(("age_days", "expected"), [(NEW_PRODUCT_DAYS, True), (8, False)])
    def test_new_badge_depends_on_age(self, age_days: int, expected: bool) -> None:
        product = ProductFactory.create()
        ProductVariantFactory.create(product=product)
        now = product.created_at + timedelta(days=age_days)

        product = selectors.catalog_products().get(pk=product.pk)

        assert ProductCard.from_product(product, now=now).is_new is expected

    def test_uses_cover_photo_and_alt_text(self) -> None:
        product = ProductFactory.create(name="Vestido")
        ProductImageFactory.create(product=product, position=2, alt_text="Costas")
        cover = ProductImageFactory.create(product=product, position=1, alt_text="")

        card = card_for(product)

        assert card.image_url == cover.image.url
        assert card.image_srcset == f"{cover.image.url} 400w, {cover.image.url} 800w"
        assert card.image_alt == "Vestido"

    def test_without_photo_has_empty_image(self) -> None:
        card = card_for(ProductFactory.create())

        assert card.image_url == ""
        assert card.image_srcset == ""


class TestProductListView:
    def test_home_shows_hero_and_cards(self, client: Client) -> None:
        product = ProductFactory.create(name="Saia Midi", created_at=timezone.now())
        ProductVariantFactory.create(product=product, size=SizeFactory.create(name="M"))
        ProductImageFactory.create(product=product)

        response = client.get(URL)

        content = response.content.decode()
        assert response.status_code == 200
        assert "Peças novas toda semana" in content
        assert "Saia Midi" in content
        assert "Novidade" in content
        assert "Tamanhos disponíveis: M" in content

    def test_sold_out_product_is_shown_with_badge(self, client: Client) -> None:
        ProductFactory.create(name="Blusa Esgotada")

        content = client.get(URL).content.decode()

        assert "Blusa Esgotada" in content
        assert "Esgotado" in content

    def test_category_page_filters_and_hides_hero(self, client: Client) -> None:
        dresses = CategoryFactory.create(name="Vestidos")
        ProductFactory.create(name="Vestido Longo", category=dresses)
        ProductFactory.create(name="Calça Reta")

        response = client.get(URL, {"categoria": dresses.slug})

        content = response.content.decode()
        assert "Vestido Longo" in content
        assert "Calça Reta" not in content
        assert "Peças novas toda semana" not in content
        assert 'aria-current="page">Vestidos' in content

    @pytest.mark.parametrize("slug", ["nao-existe", "oculta"])
    def test_unknown_or_hidden_category_is_404(self, client: Client, slug: str) -> None:
        CategoryFactory.create(name="Oculta", is_active=False)

        assert client.get(URL, {"categoria": slug}).status_code == 404

    def test_paginates_twelve_per_page(self, client: Client) -> None:
        ProductFactory.create_batch(13)

        first = client.get(URL)
        second = client.get(URL, {"page": 2})

        assert len(first.context["cards"]) == 12
        assert "Ver mais peças" in first.content.decode()
        assert len(second.context["cards"]) == 1
        assert "Peças anteriores" in second.content.decode()

    def test_empty_catalog_points_to_instagram(self, client: Client) -> None:
        content = client.get(URL).content.decode()

        assert "As peças desta semana estão chegando." in content
        assert "instagram.com/taymodas23" in content

    def test_footer_shows_delivery_info_when_set(self, client: Client) -> None:
        from apps.core.models import StoreSettings

        settings = StoreSettings.load()
        settings.delivery_info = "[PLACEHOLDER] texto de entrega"
        settings.save()

        assert "[PLACEHOLDER] texto de entrega" in client.get(URL).content.decode()

    def test_query_count_does_not_grow_with_products(self, client: Client) -> None:
        from django.db import connection

        from apps.core.models import StoreSettings

        StoreSettings.load()  # a 1ª request criaria o registro e distorceria a contagem

        def count_queries() -> int:
            with CaptureQueriesContext(connection) as ctx:
                client.get(URL)
            return len(ctx.captured_queries)

        for _ in range(2):
            product = ProductFactory.create()
            ProductImageFactory.create(product=product)
            ProductVariantFactory.create(product=product)
        baseline = count_queries()
        for _ in range(5):
            product = ProductFactory.create()
            ProductImageFactory.create(product=product)
            ProductVariantFactory.create(product=product)

        assert count_queries() == baseline


class TestSeedDemo:
    def test_refuses_to_run_without_debug(self) -> None:
        with pytest.raises(CommandError, match="DEBUG=True"):
            call_command("seed_demo")

    @override_settings(DEBUG=True)
    def test_creates_demo_products(self) -> None:
        call_command("seed_demo", count=4, stdout=None)

        assert Product.objects.count() == 4
        assert Product.objects.in_stock().count() == 3
        assert all(p.category.name == "Demo" for p in Product.objects.all())
