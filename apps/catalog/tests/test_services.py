from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest

from apps.catalog.models import ProductVariant
from apps.catalog.services import build_whatsapp_order_url, select_variant
from apps.core.models import StoreSettings

from .factories import ColorFactory, ProductFactory, ProductVariantFactory, SizeFactory

pytestmark = pytest.mark.django_db

PRODUCT_URL = "https://taymodas.example/p/vestido-midi/"


def message_of(url: str) -> str:
    return parse_qs(urlsplit(url).query)["text"][0]


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


class TestBuildWhatsappOrderUrl:
    @pytest.fixture
    def variant(self) -> ProductVariant:
        product = ProductFactory.create(name="Vestido Midi", price=Decimal("189.9"))
        return ProductVariantFactory.create(
            product=product,
            size=SizeFactory.create(name="M"),
            color=ColorFactory.create(name="Preto"),
        )

    @pytest.fixture
    def store(self) -> StoreSettings:
        return StoreSettings(whatsapp_number="5511900000000")

    def test_fills_default_message(self, variant: ProductVariant, store: StoreSettings) -> None:
        url = build_whatsapp_order_url(variant, store, PRODUCT_URL)

        assert url is not None
        assert url.startswith("https://wa.me/5511900000000?text=")
        assert message_of(url) == (
            "Olá! Quero pedir este produto:\n"
            "Vestido Midi\n"
            "Tamanho: M\n"
            "Cor: Preto\n"
            "Preço: R$ 189,90\n"
            f"{PRODUCT_URL}"
        )

    def test_uses_custom_message(self, variant: ProductVariant, store: StoreSettings) -> None:
        store.order_message_template = "Oi, {produto} tam. {tamanho} & cor {cor}?"

        url = build_whatsapp_order_url(variant, store, PRODUCT_URL)

        assert url is not None
        assert message_of(url) == "Oi, Vestido Midi tam. M & cor Preto?"

    @pytest.mark.parametrize("template", ["Quero {", "Quero {}", "Quero {produto.x}", "{nome}"])
    def test_broken_message_falls_back_to_default(
        self, variant: ProductVariant, store: StoreSettings, template: str
    ) -> None:
        store.order_message_template = template

        url = build_whatsapp_order_url(variant, store, PRODUCT_URL)

        assert url is not None
        assert message_of(url).startswith("Olá! Quero pedir este produto:")

    def test_without_number_returns_none(self, variant: ProductVariant) -> None:
        assert build_whatsapp_order_url(variant, StoreSettings(), PRODUCT_URL) is None
