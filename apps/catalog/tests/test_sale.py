"""Promoção: preço promocional por peça, com data de término opcional."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.cart.services import build_lines, cart_variants
from apps.catalog.models import Product
from apps.core.models import StoreSettings

from .factories import CategoryFactory, ProductFactory, ProductVariantFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse("catalog:product_list")
TODAY = date(2026, 10, 28)


def on_sale(name: str = "Vestido Midi", ends: date | None = None, **fields: object) -> Product:
    product = ProductFactory.create(
        name=name, price=Decimal("160"), sale_price=Decimal("120"), sale_ends_at=ends, **fields
    )
    ProductVariantFactory.create(product=product)
    return product


class TestProductSale:
    def test_without_sale_price_uses_normal_price(self) -> None:
        product = ProductFactory.build(price=Decimal("160"))

        assert not product.is_on_sale(TODAY)
        assert product.current_price(TODAY) == Decimal("160")

    @pytest.mark.parametrize(
        ("ends", "expected"),
        [(None, True), (TODAY, True), (TODAY + timedelta(1), True), (TODAY - timedelta(1), False)],
    )
    def test_end_date_is_the_last_day(self, ends: date | None, expected: bool) -> None:
        product = on_sale(ends=ends)

        assert product.is_on_sale(TODAY) is expected
        assert product.current_price(TODAY) == (Decimal("120") if expected else Decimal("160"))
        assert Product.objects.on_sale(TODAY).filter(pk=product.pk).exists() is expected

    @pytest.mark.parametrize("sale_price", ["160", "200"])
    def test_sale_price_must_be_lower(self, sale_price: str) -> None:
        product = ProductFactory.create(price=Decimal("160"), sale_price=Decimal(sale_price))

        with pytest.raises(ValidationError, match="menor que o preço normal"):
            product.full_clean()

    def test_end_date_needs_sale_price(self) -> None:
        product = ProductFactory.create(sale_ends_at=TODAY)

        with pytest.raises(ValidationError, match="preço promocional"):
            product.full_clean()


class TestStorefront:
    def test_card_shows_badge_and_struck_price(self, client: Client) -> None:
        on_sale()

        content = client.get(LIST_URL).content.decode()

        assert "photo-tag--sale" in content and ">Promoção<" in content
        assert "R$ 120,00" in content
        assert "<s" in content and "R$ 160,00</s>" in content

    def test_expired_sale_shows_normal_price(self, client: Client) -> None:
        on_sale(ends=timezone.localdate() - timedelta(1))

        content = client.get(LIST_URL).content.decode()

        assert "R$ 160,00" in content
        assert "R$ 120,00" not in content
        assert "?promocao=1" not in content

    def test_sale_shortcut_lists_only_sale_pieces(self, client: Client) -> None:
        on_sale("Peça em promoção")
        ProductVariantFactory.create(product=ProductFactory.create(name="Peça normal"))

        home = client.get(LIST_URL).content.decode()
        sales = client.get(LIST_URL, {"promocao": "1"}).content.decode()

        assert 'href="/?promocao=1"' in home
        assert "Peça em promoção" in sales and "Peça normal" not in sales
        assert "<title>Promoções — Tay Modas</title>" in sales
        assert 'rel="canonical" href="http://testserver/?promocao=1"' in sales
        assert 'id="titulo-inicio"' not in sales
        assert '<input type="hidden" name="promocao" value="1">' in sales

    def test_sale_shortcut_hidden_without_sales(self, client: Client) -> None:
        ProductVariantFactory.create(product=ProductFactory.create())

        assert "?promocao=1" not in client.get(LIST_URL).content.decode()

    def test_empty_sale_page_explains(self, client: Client) -> None:
        content = client.get(LIST_URL, {"promocao": "1"}).content.decode()

        assert "Nenhuma peça em promoção agora." in content

    def test_sale_inside_category_keeps_category_title(self, client: Client) -> None:
        dresses = CategoryFactory.create(name="Vestidos")
        on_sale(category=dresses)

        content = client.get(LIST_URL, {"categoria": dresses.slug, "promocao": "1"}).content
        assert "<h1" in content.decode() and "Vestidos</h1>" in content.decode()

    def test_detail_shows_sale_price(self, client: Client) -> None:
        product = on_sale()

        content = client.get(product.get_absolute_url()).content.decode()

        assert 'content="120.00"' in content
        assert "R$ 160,00</s>" in content
        assert ">Promoção</span>" in content

    def test_cart_charges_sale_price(self) -> None:
        product = on_sale()
        variant = product.variants.get()
        variant.stock = 2
        variant.save()
        items = {variant.pk: 2}

        [line] = build_lines(items, cart_variants(items))

        assert line.subtotal == Decimal("240")


class TestAdmin:
    def test_changelist_shows_sale_and_filters(self, admin_client: Client) -> None:
        StoreSettings.load()
        on_sale("Peça em promoção")
        ProductFactory.create(name="Peça normal")
        url = reverse("admin:catalog_product_changelist")

        content = admin_client.get(url).content.decode()
        filtered = admin_client.get(url, {"promocao": "sim"}).content.decode()

        assert "<strong>R$ 120,00</strong> <s>R$ 160,00</s>" in content
        assert "Peça em promoção" in filtered and "Peça normal" not in filtered

    def test_add_form_has_sale_fields(self, admin_client: Client) -> None:
        content = admin_client.get(reverse("admin:catalog_product_add")).content.decode()

        assert 'name="sale_price"' in content and 'name="sale_ends_at"' in content
