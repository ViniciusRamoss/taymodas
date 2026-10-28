import pytest

from apps.catalog.models import ProductVariant
from apps.catalog.services import select_variant

from .factories import ColorFactory, ProductFactory, ProductVariantFactory, SizeFactory

pytestmark = pytest.mark.django_db


class TestSelectVariant:
    @pytest.fixture
    def variants(self) -> list[ProductVariant]:
        """P e M em Preto; M em Vinho esgotado; G só em Vinho."""
        product = ProductFactory.create()
        small, medium, large = (
            SizeFactory.create(name="P", position=1),
            SizeFactory.create(name="M", position=2),
            SizeFactory.create(name="G", position=3),
        )
        black, wine = ColorFactory.create(name="Preto"), ColorFactory.create(name="Vinho")
        return [
            ProductVariantFactory.create(product=product, size=large, color=wine, stock=1),
            ProductVariantFactory.create(product=product, size=small, color=black, stock=2),
            ProductVariantFactory.create(product=product, size=medium, color=black, stock=1),
            ProductVariantFactory.create(product=product, size=medium, color=wine, stock=0),
        ]

    def test_without_choice_lists_options_in_order(self, variants: list[ProductVariant]) -> None:
        selection = select_variant(variants, size_id=None, color_id=None)

        assert [c.name for c in selection.sizes] == ["P", "M", "G"]
        assert [c.name for c in selection.colors] == ["Preto", "Vinho"]
        assert all(c.is_available for c in selection.sizes + selection.colors)
        assert selection.variant is None
        assert selection.is_sold_out_combination is False

    def test_color_limits_available_sizes(self, variants: list[ProductVariant]) -> None:
        wine = variants[0].color

        selection = select_variant(variants, size_id=None, color_id=wine.pk)

        assert {c.name: c.is_available for c in selection.sizes} == {
            "P": False,
            "M": False,
            "G": True,
        }
        assert selection.color == wine

    def test_full_choice_returns_variant(self, variants: list[ProductVariant]) -> None:
        medium_black = variants[2]

        selection = select_variant(
            variants, size_id=medium_black.size.pk, color_id=medium_black.color.pk
        )

        assert selection.variant == medium_black
        assert [c.name for c in selection.sizes if c.is_selected] == ["M"]

    def test_sold_out_combination_has_no_variant(self, variants: list[ProductVariant]) -> None:
        medium_wine = variants[3]

        selection = select_variant(
            variants, size_id=medium_wine.size.pk, color_id=medium_wine.color.pk
        )

        assert selection.variant is None
        assert selection.is_sold_out_combination is True

    def test_ignores_ids_of_other_products(self, variants: list[ProductVariant]) -> None:
        selection = select_variant(
            variants, size_id=SizeFactory.create().pk, color_id=ColorFactory.create().pk
        )

        assert selection.size is None
        assert selection.color is None

    def test_single_option_is_preselected(self) -> None:
        variant = ProductVariantFactory.create()

        selection = select_variant([variant], size_id=None, color_id=None)

        assert selection.variant == variant
