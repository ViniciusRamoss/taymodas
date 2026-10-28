import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.catalog import selectors
from apps.catalog.models import Color, Size
from apps.core.models import StoreSettings

from .factories import (
    CategoryFactory,
    ColorFactory,
    ProductFactory,
    ProductVariantFactory,
    SizeFactory,
)

HERO_MARKER = 'id="titulo-inicio"'

pytestmark = pytest.mark.django_db

URL = reverse("catalog:product_list")
HTMX = {"HX-Request": "true"}


@pytest.fixture
def sizes() -> dict[str, Size]:
    return {name: SizeFactory.create(name=name) for name in ("P", "M", "G")}


@pytest.fixture
def colors() -> dict[str, Color]:
    return {name: ColorFactory.create(name=name) for name in ("Preto", "Vinho")}


@pytest.fixture
def catalog(sizes: dict[str, Size], colors: dict[str, Color]) -> None:
    """Vestido: P/Preto e M/Vinho. Blusa: M/Preto. Saia: G/Vinho esgotada."""
    dresses = CategoryFactory.create(name="Vestidos")
    tops = CategoryFactory.create(name="Blusas")
    dress = ProductFactory.create(name="Vestido Longo", category=dresses)
    ProductVariantFactory.create(product=dress, size=sizes["P"], color=colors["Preto"])
    ProductVariantFactory.create(product=dress, size=sizes["M"], color=colors["Vinho"])
    top = ProductFactory.create(name="Blusa Seda", category=tops)
    ProductVariantFactory.create(product=top, size=sizes["M"], color=colors["Preto"])
    skirt = ProductFactory.create(name="Saia Plissada", category=dresses)
    ProductVariantFactory.create(product=skirt, size=sizes["G"], color=colors["Vinho"], stock=0)


def names(client: Client, params: dict[str, str | int]) -> set[str]:
    response = client.get(URL, params)
    return {card.name for card in response.context["cards"]}


@pytest.mark.usefixtures("catalog")
class TestSelectors:
    def test_size_and_color_must_match_the_same_variant(
        self, sizes: dict[str, Size], colors: dict[str, Color]
    ) -> None:
        products = selectors.catalog_products(size=sizes["M"], color=colors["Preto"])

        assert [p.name for p in products] == ["Blusa Seda"]

    def test_size_filter_hides_sold_out(self, sizes: dict[str, Size]) -> None:
        assert list(selectors.catalog_products(size=sizes["G"])) == []

    def test_options_only_include_stock_in_category(self) -> None:
        dresses = CategoryFactory.create(name="Vestidos")

        sizes, colors = selectors.filter_options(dresses)

        assert [s.name for s in sizes] == ["P", "M"]
        assert [c.name for c in colors] == ["Preto", "Vinho"]


@pytest.mark.usefixtures("catalog")
class TestListFilters:
    def test_filters_by_size(self, client: Client, sizes: dict[str, Size]) -> None:
        assert names(client, {"tamanho": sizes["M"].pk}) == {"Vestido Longo", "Blusa Seda"}

    def test_combines_category_size_and_color(
        self, client: Client, sizes: dict[str, Size], colors: dict[str, Color]
    ) -> None:
        params: dict[str, str | int] = {
            "categoria": "vestidos",
            "tamanho": sizes["M"].pk,
            "cor": colors["Vinho"].pk,
        }

        assert names(client, params) == {"Vestido Longo"}

    def test_unknown_ids_are_ignored(self, client: Client) -> None:
        assert names(client, {"tamanho": "999", "cor": "abc"}) == {
            "Vestido Longo",
            "Blusa Seda",
            "Saia Plissada",
        }

    def test_selected_option_and_clear_link(self, client: Client, sizes: dict[str, Size]) -> None:
        params: dict[str, str | int] = {"categoria": "vestidos", "tamanho": sizes["P"].pk}
        html = client.get(URL, params).content.decode()

        assert f'value="{sizes["P"].pk}" selected' in html
        assert 'href="/?categoria=vestidos"' in html
        assert "Limpar filtros" in html

    def test_filters_hide_hero_and_use_h1(self, client: Client, sizes: dict[str, Size]) -> None:
        html = client.get(URL, {"tamanho": sizes["P"].pk}).content.decode()

        assert HERO_MARKER not in html
        assert '<h1 id="titulo-lista"' in html

    def test_empty_result_offers_to_clear(
        self, client: Client, sizes: dict[str, Size], colors: dict[str, Color]
    ) -> None:
        html = client.get(
            URL, {"tamanho": sizes["P"].pk, "cor": colors["Vinho"].pk}
        ).content.decode()

        assert "Nenhuma peça disponível com esse filtro." in html

    def test_pagination_keeps_filters(self, client: Client, sizes: dict[str, Size]) -> None:
        for _ in range(12):
            ProductVariantFactory.create(size=sizes["P"])

        html = client.get(URL, {"tamanho": sizes["P"].pk}).content.decode()

        assert f"?tamanho={sizes['P'].pk}&amp;page=2" in html


@pytest.mark.usefixtures("catalog")
class TestHtmx:
    def test_returns_catalog_block_with_title_and_header_oob(
        self, client: Client, sizes: dict[str, Size]
    ) -> None:
        response = client.get(URL, {"categoria": "vestidos"}, headers=HTMX)

        html = response.content.decode()
        assert "<html" not in html
        assert "<title>Vestidos — Tay Modas</title>" in html
        assert 'id="catalogo"' in html
        assert 'id="topo" hx-swap-oob="true"' in html
        assert HERO_MARKER not in html
        assert "HX-Request" in response["Vary"]

    def test_unfiltered_first_page_brings_hero_back(self, client: Client) -> None:
        html = client.get(URL, headers=HTMX).content.decode()

        assert HERO_MARKER in html

    def test_history_restore_gets_full_page(self, client: Client) -> None:
        response = client.get(URL, headers={**HTMX, "HX-History-Restore-Request": "true"})

        assert "<html" in response.content.decode()


def test_query_count_does_not_grow_with_options(client: Client) -> None:
    StoreSettings.load()

    def count_queries() -> int:
        with CaptureQueriesContext(connection) as ctx:
            client.get(URL)
        return len(ctx.captured_queries)

    ProductVariantFactory.create()
    baseline = count_queries()
    for _ in range(4):
        ProductVariantFactory.create()

    assert count_queries() == baseline
