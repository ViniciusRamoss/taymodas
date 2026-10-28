"""Dados prontos para exibir um produto nos templates, sem lógica no HTML."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone

from apps.core.formatting import format_brl
from apps.core.images import image_url

from .models import Category, Color, Product, ProductImage, ProductVariant, Size

# Peças cadastradas nos últimos dias ganham o selo "Novidade" (lançamentos são semanais).
NEW_PRODUCT_DAYS = 7
CARD_IMAGE_WIDTHS = (400, 800)
DETAIL_IMAGE_WIDTHS = (600, 1200)
# Prévia em WhatsApp/Instagram/Facebook: 1200px de largura é o recomendado pelo Open Graph.
SHARE_IMAGE_WIDTH = 1200


def _srcset(image: ProductImage, widths: tuple[int, ...]) -> str:
    return ", ".join(f"{image_url(image.image, width=width)} {width}w" for width in widths)


@dataclass(frozen=True)
class ColorSwatch:
    name: str
    hex_code: str


@dataclass(frozen=True)
class GalleryImage:
    url: str
    srcset: str
    alt: str
    share_url: str


@dataclass(frozen=True)
class ProductDetail:
    name: str
    price: str
    original_price: str
    price_amount: str
    description: str
    category_name: str
    category_slug: str
    images: tuple[GalleryImage, ...]

    @classmethod
    def from_product(cls, product: Product) -> ProductDetail:
        """Monta a página a partir de um produto vindo de `selectors.product_details`."""
        images = tuple(
            GalleryImage(
                url=image_url(image.image, width=DETAIL_IMAGE_WIDTHS[0]),
                srcset=_srcset(image, DETAIL_IMAGE_WIDTHS),
                alt=image.alt_text or product.name,
                share_url=image_url(image.image, width=SHARE_IMAGE_WIDTH),
            )
            for image in product.images.all()
        )
        price = product.current_price()
        return cls(
            name=product.name,
            price=format_brl(price),
            original_price=format_brl(product.price) if product.is_on_sale() else "",
            price_amount=f"{price:.2f}",
            description=product.description,
            category_name=product.category.name,
            category_slug=product.category.slug,
            images=images,
        )


@dataclass(frozen=True)
class ProductCard:
    name: str
    url: str
    price: str
    original_price: str
    image_url: str
    image_srcset: str
    image_alt: str
    sizes: tuple[str, ...]
    colors: tuple[ColorSwatch, ...]
    is_sold_out: bool
    is_new: bool
    is_on_sale: bool

    @classmethod
    def from_product(cls, product: Product, *, now: datetime | None = None) -> ProductCard:
        """Monta o card a partir de um produto vindo de `selectors.catalog_products`."""
        now = now or timezone.now()
        variants: list[ProductVariant] = product.available_variants  # type: ignore[attr-defined]
        images = list(product.images.all())
        cover = images[0] if images else None

        url, srcset, alt = "", "", product.name
        if cover is not None:
            url = image_url(cover.image, width=CARD_IMAGE_WIDTHS[0])
            srcset = _srcset(cover, CARD_IMAGE_WIDTHS)
            alt = cover.alt_text or product.name

        sizes = sorted({v.size for v in variants}, key=lambda size: (size.position, size.name))
        colors = sorted({v.color for v in variants}, key=lambda color: color.name)
        is_sold_out = not variants
        today = timezone.localdate(now)
        is_on_sale = product.is_on_sale(today)

        return cls(
            name=product.name,
            url=product.get_absolute_url(),
            price=format_brl(product.current_price(today)),
            original_price=format_brl(product.price) if is_on_sale else "",
            image_url=url,
            image_srcset=srcset,
            image_alt=alt,
            sizes=tuple(size.name for size in sizes),
            colors=tuple(ColorSwatch(color.name, color.hex_code) for color in colors),
            is_sold_out=is_sold_out,
            is_new=not is_sold_out and now - product.created_at <= timedelta(NEW_PRODUCT_DAYS),
            is_on_sale=is_on_sale,
        )


@dataclass(frozen=True)
class CatalogFilters:
    """Filtros da listagem: opções com estoque, o que está escolhido e as URLs derivadas."""

    sizes: tuple[Size, ...]
    colors: tuple[Color, ...]
    size: Size | None
    color: Color | None
    clear_url: str
    query_prefix: str

    @property
    def is_active(self) -> bool:
        return self.size is not None or self.color is not None

    @classmethod
    def build(
        cls,
        *,
        category: Category | None,
        sizes: Sequence[Size],
        colors: Sequence[Color],
        size_id: int | None,
        color_id: int | None,
        on_sale: bool = False,
    ) -> CatalogFilters:
        size = next((s for s in sizes if s.pk == size_id), None)
        color = next((c for c in colors if c.pk == color_id), None)
        base = {
            **({"categoria": category.slug} if category is not None else {}),
            **({"promocao": "1"} if on_sale else {}),
        }
        params = {
            **base,
            **({"tamanho": str(size.pk)} if size is not None else {}),
            **({"cor": str(color.pk)} if color is not None else {}),
        }
        list_url = reverse("catalog:product_list")
        return cls(
            sizes=tuple(sizes),
            colors=tuple(colors),
            size=size,
            color=color,
            clear_url=f"{list_url}?{urlencode(base)}" if base else list_url,
            # Prefixo da querystring da paginação: "categoria=x&tamanho=1&" ou "".
            query_prefix=f"{urlencode(params)}&" if params else "",
        )
