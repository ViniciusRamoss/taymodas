"""Regras de negócio do catálogo. Funções puras: recebem dados já carregados, sem queries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from apps.core.formatting import format_brl
from apps.core.models import DEFAULT_ORDER_MESSAGE, StoreSettings

from .models import Color, ProductVariant, Size


@dataclass(frozen=True)
class Choice:
    """Uma opção de tamanho ou cor na página do produto."""

    id: int
    name: str
    hex_code: str
    is_available: bool
    is_selected: bool


@dataclass(frozen=True)
class VariantSelection:
    sizes: tuple[Choice, ...]
    colors: tuple[Choice, ...]
    size: Size | None
    color: Color | None
    variant: ProductVariant | None

    @property
    def is_sold_out_combination(self) -> bool:
        """Tamanho e cor escolhidos, mas essa combinação está sem estoque."""
        return self.size is not None and self.color is not None and self.variant is None


def select_variant(
    variants: Sequence[ProductVariant], *, size_id: int | None, color_id: int | None
) -> VariantSelection:
    """Resolve a escolha de tamanho e cor da cliente.

    `variants` são todas as variantes do produto, com `size` e `color` carregados.
    Ids que não pertencem ao produto são ignorados. Se o produto tem um único tamanho
    (ou cor), ele já vem escolhido. Uma opção fica indisponível quando não há estoque
    para ela combinada com o que já foi escolhido na outra dimensão.
    """
    sizes = sorted({v.size for v in variants}, key=lambda size: (size.position, size.name))
    colors = sorted({v.color for v in variants}, key=lambda color: color.name)
    size = _pick(sizes, size_id)
    color = _pick(colors, color_id)
    in_stock = [v for v in variants if v.is_in_stock]

    def size_available(candidate: Size) -> bool:
        return any(
            v.size_id == candidate.pk and (color is None or v.color_id == color.pk)
            for v in in_stock
        )

    def color_available(candidate: Color) -> bool:
        return any(
            v.color_id == candidate.pk and (size is None or v.size_id == size.pk) for v in in_stock
        )

    variant = None
    if size is not None and color is not None:
        variant = next(
            (v for v in in_stock if v.size_id == size.pk and v.color_id == color.pk), None
        )

    return VariantSelection(
        sizes=tuple(Choice(s.pk, s.name, "", size_available(s), s == size) for s in sizes),
        colors=tuple(
            Choice(c.pk, c.name, c.hex_code, color_available(c), c == color) for c in colors
        ),
        size=size,
        color=color,
        variant=variant,
    )


def _pick[T: (Size, Color)](options: list[T], selected_id: int | None) -> T | None:
    if len(options) == 1:
        return options[0]
    return next((option for option in options if option.pk == selected_id), None)


def build_whatsapp_order_url(
    variant: ProductVariant, store: StoreSettings, product_url: str
) -> str | None:
    """Link do WhatsApp com a mensagem de pedido já escrita.

    Devolve `None` enquanto a loja não cadastrou o número (o botão não aparece).
    """
    fields = {
        "produto": variant.product.name,
        "tamanho": variant.size.name,
        "cor": variant.color.name,
        "preco": format_brl(variant.product.price),
        "link": product_url,
    }
    try:
        text = store.order_message_template.format_map(fields)
    except (KeyError, IndexError, ValueError, AttributeError):
        # Mensagem salva com chaves inválidas (ex.: "{" solto): usa a padrão para não
        # deixar a cliente sem botão de pedido.
        text = DEFAULT_ORDER_MESSAGE.format_map(fields)
    return store.whatsapp_url(text)
