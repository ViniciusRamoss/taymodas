from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.catalog.models import Category, Color, Product, ProductImage, ProductVariant

from .factories import (
    CategoryFactory,
    ColorFactory,
    ProductFactory,
    ProductImageFactory,
    ProductVariantFactory,
    SizeFactory,
)

pytestmark = pytest.mark.django_db


class TestCategory:
    def test_slug_is_generated_from_name(self) -> None:
        category = CategoryFactory.create(name="Vestidos Longos")

        assert category.slug == "vestidos-longos"
        assert str(category) == "Vestidos Longos"

    def test_ordering_uses_position_then_name(self) -> None:
        second = CategoryFactory.create(name="A", position=2)
        first = CategoryFactory.create(name="B", position=1)

        assert list(Category.objects.all()) == [first, second]


class TestColor:
    @pytest.mark.parametrize("hex_code", ["#000000", "#d4af37", ""])
    def test_accepts_valid_hex_or_blank(self, hex_code: str) -> None:
        Color(name="Teste", hex_code=hex_code).full_clean()

    @pytest.mark.parametrize("hex_code", ["000000", "#fff", "#GGGGGG"])
    def test_rejects_invalid_hex(self, hex_code: str) -> None:
        with pytest.raises(ValidationError, match="#RRGGBB"):
            Color(name="Teste", hex_code=hex_code).full_clean()


class TestProduct:
    def test_slug_is_generated_and_unique(self) -> None:
        first = ProductFactory.create(name="Vestido Floral")
        second = ProductFactory.create(name="Vestido Floral")

        assert first.slug == "vestido-floral"
        assert second.slug == "vestido-floral-2"

    def test_slug_is_kept_when_name_changes(self) -> None:
        product = ProductFactory.create(name="Saia Midi")
        product.name = "Saia Midi Plissada"
        product.save()

        assert product.slug == "saia-midi"

    def test_slug_respects_max_length_with_suffix(self) -> None:
        long_name = "a" * 200
        ProductFactory.create(name=long_name)
        product = ProductFactory.create(name=long_name)

        assert len(product.slug) <= 140
        assert product.slug.endswith("-2")

    @pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1")])
    def test_rejects_non_positive_price(self, price: Decimal) -> None:
        product = ProductFactory.build(price=price, category=CategoryFactory.create())

        with pytest.raises(ValidationError) as exc:
            product.full_clean()

        assert "price" in exc.value.message_dict

    def test_category_with_products_cannot_be_deleted(self) -> None:
        product = ProductFactory.create()

        with pytest.raises(ProtectedError):
            product.category.delete()

    def test_active_excludes_inactive_products_and_categories(self) -> None:
        visible = ProductFactory.create()
        ProductFactory.create(is_active=False)
        ProductFactory.create(category=CategoryFactory.create(is_active=False))

        assert list(Product.objects.active()) == [visible]

    def test_with_total_stock_sums_variants_and_defaults_to_zero(self) -> None:
        product = ProductFactory.create()
        ProductVariantFactory.create(product=product, stock=2)
        ProductVariantFactory.create(product=product, stock=3)
        without_variants = ProductFactory.create()

        # `total_stock` é anotação do queryset; o django-stubs não a enxerga no model.
        stocks = {p.pk: p.total_stock for p in Product.objects.with_total_stock()}  # type: ignore[attr-defined]

        assert stocks == {product.pk: 5, without_variants.pk: 0}

    def test_deleting_product_removes_images_and_variants(self) -> None:
        product = ProductFactory.create()
        ProductImageFactory.create(product=product)
        ProductVariantFactory.create(product=product)

        product.delete()

        assert not ProductVariant.objects.exists()
        assert not ProductImage.objects.exists()


class TestProductImage:
    def test_images_are_ordered_by_position(self) -> None:
        product = ProductFactory.create()
        back = ProductImageFactory.create(product=product, position=2)
        cover = ProductImageFactory.create(product=product, position=1)

        assert list(product.images.all()) == [cover, back]
        assert str(cover) == f"Foto 1 de {product}"


class TestProductVariant:
    def test_str_shows_size_and_color(self) -> None:
        variant = ProductVariantFactory.create(
            size=SizeFactory.create(name="M"), color=ColorFactory.create(name="Preto")
        )

        assert str(variant) == "M / Preto"

    @pytest.mark.parametrize(("stock", "expected"), [(0, False), (1, True)])
    def test_is_in_stock(self, stock: int, expected: bool) -> None:
        assert ProductVariantFactory.build(stock=stock).is_in_stock is expected

    def test_same_size_and_color_cannot_repeat_on_product(self) -> None:
        variant = ProductVariantFactory.create()

        with pytest.raises(IntegrityError):
            ProductVariantFactory.create(
                product=variant.product, size=variant.size, color=variant.color
            )

    def test_duplicate_variant_has_friendly_validation_message(self) -> None:
        variant = ProductVariantFactory.create()
        duplicate = ProductVariant(
            product=variant.product, size=variant.size, color=variant.color, stock=1
        )

        with pytest.raises(ValidationError, match="já tem essa combinação"):
            duplicate.full_clean()

    def test_sizes_are_reusable_across_products(self) -> None:
        size = SizeFactory.create(name="G")
        color = ColorFactory.create(name="Preto")

        ProductVariantFactory.create(size=size, color=color)
        ProductVariantFactory.create(size=size, color=color)

        assert size.variants.count() == 2

    def test_size_in_use_cannot_be_deleted(self) -> None:
        variant = ProductVariantFactory.create()

        with pytest.raises(ProtectedError):
            variant.size.delete()

    def test_variants_are_ordered_by_size_position(self) -> None:
        product = ProductFactory.create()
        large = ProductVariantFactory.create(
            product=product, size=SizeFactory.create(name="G", position=3)
        )
        small = ProductVariantFactory.create(
            product=product, size=SizeFactory.create(name="P", position=1)
        )

        assert list(product.variants.all()) == [small, large]


class TestProductStockQueries:
    def test_in_stock_and_sold_out_split_products(self) -> None:
        available = ProductFactory.create()
        ProductVariantFactory.create(product=available, stock=0)
        ProductVariantFactory.create(product=available, stock=1)
        sold_out = ProductFactory.create()
        ProductVariantFactory.create(product=sold_out, stock=0)
        without_variants = ProductFactory.create()

        assert list(Product.objects.in_stock()) == [available]
        assert set(Product.objects.sold_out()) == {sold_out, without_variants}

    def test_total_stock_is_not_inflated_by_variant_filters(self) -> None:
        product = ProductFactory.create()
        size = SizeFactory.create(name="M")
        ProductVariantFactory.create(product=product, size=size, stock=2)
        ProductVariantFactory.create(
            product=product, size=size, color=ColorFactory.create(), stock=3
        )
        ProductVariantFactory.create(product=product, stock=4)

        queryset = Product.objects.with_total_stock().filter(variants__size=size).distinct()

        assert [p.total_stock for p in queryset] == [9]  # type: ignore[attr-defined]
