"""Dados prontos para exibir um produto nos templates, sem lógica no HTML."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.utils import timezone

from apps.core.formatting import format_brl
from apps.core.images import image_url

from .models import Product, ProductImage, ProductVariant

# Peças cadastradas nos últimos dias ganham o selo "Novidade" (lançamentos são semanais).
NEW_PRODUCT_DAYS = 7
CARD_IMAGE_WIDTHS = (400, 800)
DETAIL_IMAGE_WIDTHS = (600, 1200)


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


@dataclass(frozen=True)
class ProductDetail:
    name: str
    price: str
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
            )
            for image in product.images.all()
        )
        return cls(
            name=product.name,
            price=format_brl(product.price),
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
    image_url: str
    image_srcset: str
    image_alt: str
    sizes: tuple[str, ...]
    colors: tuple[ColorSwatch, ...]
    is_sold_out: bool
    is_new: bool

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

        return cls(
            name=product.name,
            url=product.get_absolute_url(),
            price=format_brl(product.price),
            image_url=url,
            image_srcset=srcset,
            image_alt=alt,
            sizes=tuple(size.name for size in sizes),
            colors=tuple(ColorSwatch(color.name, color.hex_code) for color in colors),
            is_sold_out=is_sold_out,
            is_new=not is_sold_out and now - product.created_at <= timedelta(NEW_PRODUCT_DAYS),
        )
