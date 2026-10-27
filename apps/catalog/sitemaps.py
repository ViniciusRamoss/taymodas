from datetime import datetime

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse

from . import selectors
from .models import Category, Product


class ProductSitemap(Sitemap[Product]):
    changefreq = "weekly"

    def items(self) -> QuerySet[Product]:
        return Product.objects.active().order_by("pk")

    def lastmod(self, item: Product) -> datetime:
        return item.updated_at


class CategorySitemap(Sitemap[Category]):
    changefreq = "weekly"

    def items(self) -> QuerySet[Category]:
        return selectors.categories_with_products().order_by("pk")

    def location(self, item: Category) -> str:
        return f"{reverse('catalog:product_list')}?categoria={item.slug}"


class HomeSitemap(Sitemap[str]):
    changefreq = "daily"
    priority = 1.0

    def items(self) -> list[str]:
        return ["catalog:product_list"]

    def location(self, item: str) -> str:
        return reverse(item)


SITEMAPS = {"inicio": HomeSitemap, "categorias": CategorySitemap, "produtos": ProductSitemap}
