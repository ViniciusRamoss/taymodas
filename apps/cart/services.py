"""Monta a sacola para exibir e a mensagem do pedido para o WhatsApp."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Prefetch, QuerySet

from apps.catalog.models import Product, ProductImage, ProductVariant
from apps.core.formatting import format_brl
from apps.core.images import image_url
from apps.core.models import DEFAULT_ORDER_MESSAGE, StoreSettings

THUMB_WIDTH = 240


def cart_variants(variant_ids: Iterable[int]) -> QuerySet[ProductVariant]:
    """Variações da sacola cujo produto ainda está visível, com o que a página usa."""
    return (
        ProductVariant.objects.filter(
            pk__in=list(variant_ids), product__in=Product.objects.active()
        )
        .select_related("product", "size", "color")
        .prefetch_related(
            Prefetch("product__images", queryset=ProductImage.objects.order_by("position"))
        )
    )


@dataclass(frozen=True)
class CartLine:
    variant_id: int
    name: str
    url: str
    color: str
    size: str
    unit_price: Decimal
    quantity: int
    stock: int
    image_url: str
    image_alt: str

    @property
    def is_available(self) -> bool:
        return self.quantity > 0

    @property
    def can_add_more(self) -> bool:
        return self.quantity < self.stock

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    @property
    def subtotal_display(self) -> str:
        return format_brl(self.subtotal)

    @property
    def unit_price_display(self) -> str:
        return format_brl(self.unit_price)


def build_lines(items: dict[int, int], variants: Iterable[ProductVariant]) -> list[CartLine]:
    """Uma linha por peça da sacola, na ordem em que foram adicionadas.

    A quantidade fica limitada ao estoque atual; peça que esgotou vem com quantidade zero
    (aparece como esgotada e fica fora do total). Variações que sumiram do site são ignoradas.
    """
    by_id = {variant.pk: variant for variant in variants}
    lines = []
    for variant_id, quantity in items.items():
        variant = by_id.get(variant_id)
        if variant is None:
            continue
        product = variant.product
        images = list(product.images.all())
        cover = images[0] if images else None
        lines.append(
            CartLine(
                variant_id=variant_id,
                name=product.name,
                url=product.get_absolute_url(),
                color=variant.color.name,
                size=variant.size.name,
                unit_price=product.price,
                quantity=min(quantity, variant.stock),
                stock=variant.stock,
                image_url=image_url(cover.image, width=THUMB_WIDTH) if cover else "",
                image_alt=(cover.alt_text if cover else "") or product.name,
            )
        )
    return lines


def cart_total(lines: Iterable[CartLine]) -> Decimal:
    return sum((line.subtotal for line in lines), Decimal(0))


def build_whatsapp_cart_url(
    lines: Iterable[CartLine], store: StoreSettings, absolute_url: Callable[[str], str]
) -> str | None:
    """Link do WhatsApp com o pedido da sacola já escrito: cada peça (quantidade, cor,
    tamanho, valor e link) e o total. Peças esgotadas ficam de fora.

    Devolve `None` enquanto a loja não cadastrou o número ou a sacola não tem peça disponível.
    """
    available = [line for line in lines if line.is_available]
    if not available:
        return None
    items = "\n\n".join(
        f"• {line.quantity}x {line.name} ({line.color}, tam. {line.size}): "
        f"{line.subtotal_display}\n{absolute_url(line.url)}"
        for line in available
    )
    fields = {"itens": items, "total": format_brl(cart_total(available))}
    try:
        text = store.order_message_template.format_map(fields)
    except (KeyError, IndexError, ValueError, AttributeError):
        # Mensagem salva com chaves inválidas (ex.: "{" solto): usa a padrão para não
        # deixar a cliente sem botão de pedido.
        text = DEFAULT_ORDER_MESSAGE.format_map(fields)
    return store.whatsapp_url(text)
