"""Etapa 7: metadados de compartilhamento, páginas de erro, robots.txt e sitemap."""

import re
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from .factories import CategoryFactory, ProductFactory, ProductImageFactory, ProductVariantFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse("catalog:product_list")


def meta(html: str, prop: str) -> str | None:
    match = re.search(f'<meta (?:property|name)="{re.escape(prop)}" content="([^"]*)"', html)
    return match.group(1) if match else None


def canonical(html: str) -> str | None:
    match = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    return match.group(1) if match else None


class TestMeta:
    def test_home_has_defaults_and_no_image(self, client: Client) -> None:
        html = client.get(LIST_URL, {"tamanho": "3"}).content.decode()

        assert meta(html, "og:title") == "Tay Modas — moda feminina em Serrana-SP"
        assert meta(html, "og:type") == "website"
        assert canonical(html) == "http://testserver/"
        assert meta(html, "og:image") is None

    def test_category_canonical_keeps_only_category(self, client: Client) -> None:
        category = CategoryFactory.create(name="Vestidos")
        ProductFactory.create(category=category)

        html = client.get(LIST_URL, {"categoria": "vestidos", "page": "1"}).content.decode()

        assert "<title>Vestidos — Tay Modas</title>" in html
        assert canonical(html) == "http://testserver/?categoria=vestidos"

    def test_product_shares_cover_photo_price_and_description(self, client: Client) -> None:
        product = ProductFactory.create(
            name="Vestido Midi", price=Decimal("189.9"), description="Viscose com forro."
        )
        ProductVariantFactory.create(product=product)
        cover = ProductImageFactory.create(product=product, position=0)
        ProductImageFactory.create(product=product, position=1)

        html = client.get(product.get_absolute_url(), {"cor": "1"}).content.decode()

        assert meta(html, "og:title") == "Vestido Midi — Tay Modas"
        assert meta(html, "description") == "Viscose com forro."
        assert meta(html, "og:type") == "product"
        assert meta(html, "og:image") == f"http://testserver{cover.image.url}"
        assert meta(html, "product:price:amount") == "189.90"
        assert canonical(html) == f"http://testserver{product.get_absolute_url()}"

    def test_long_description_is_truncated(self, client: Client) -> None:
        product = ProductFactory.create(description="a" * 300)

        html = client.get(product.get_absolute_url()).content.decode()

        description = meta(html, "description")
        assert description is not None and len(description) == 160

    def test_favicon_is_linked(self, client: Client) -> None:
        assert 'rel="icon" href="/static/img/favicon.svg"' in client.get(LIST_URL).content.decode()


class TestErrorPages:
    def test_404_uses_site_layout(self, client: Client) -> None:
        response = client.get("/nao-existe/")

        html = response.content.decode()
        assert response.status_code == 404
        assert "Página não encontrada" in html
        assert "Ver todas as peças" in html

    def test_500_renders_without_database(self) -> None:
        from django.template.loader import get_template

        html = get_template("500.html").render()

        assert "O site teve um problema" in html


class TestRobotsAndSitemap:
    def test_robots_points_to_sitemap_and_hides_filters(self, client: Client) -> None:
        response = client.get("/robots.txt")

        body = response.content.decode()
        assert response["Content-Type"].startswith("text/plain")
        assert "Sitemap: http://testserver/sitemap.xml" in body
        assert "Disallow: /*?*tamanho=" in body
        assert "admin" not in body

    def test_sitemap_lists_visible_products_and_categories(self, client: Client) -> None:
        visible = ProductFactory.create(category=CategoryFactory.create(name="Vestidos"))
        hidden = ProductFactory.create(is_active=False)

        xml = client.get("/sitemap.xml").content.decode()

        assert f"http://testserver{visible.get_absolute_url()}" in xml
        assert hidden.get_absolute_url() not in xml
        assert "http://testserver/?categoria=vestidos" in xml
        assert "<loc>http://testserver/</loc>" in xml
