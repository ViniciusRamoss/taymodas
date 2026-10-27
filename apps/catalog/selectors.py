"""Consultas de leitura do catálogo público, já otimizadas para os templates."""

from django.db.models import Exists, OuterRef, Prefetch, QuerySet

from .models import Category, Color, Product, ProductVariant, Size


def catalog_products(
    category: Category | None = None, size: Size | None = None, color: Color | None = None
) -> QuerySet[Product]:
    """Produtos visíveis, com estoque primeiro e mais novos antes.

    Com `size` e/ou `color`, só entram produtos com uma variante em estoque nesse tamanho e
    nessa cor (a mesma variante); esgotados saem, já que a cliente procura algo para pedir.

    Cada produto vem com `is_available` anotado e `available_variants` (só variantes com
    estoque, com tamanho e cor) pré-carregado, para a listagem não fazer query por item.
    """
    products = Product.objects.active()
    if category is not None:
        products = products.filter(category=category)

    in_stock = ProductVariant.objects.filter(stock__gt=0)
    if size is not None or color is not None:
        matching = in_stock.filter(product=OuterRef("pk"))
        if size is not None:
            matching = matching.filter(size=size)
        if color is not None:
            matching = matching.filter(color=color)
        products = products.filter(Exists(matching))

    return (
        products.annotate(is_available=Exists(in_stock.filter(product=OuterRef("pk"))))
        .select_related("category")
        .prefetch_related(
            "images",
            Prefetch(
                "variants",
                queryset=in_stock.select_related("size", "color"),
                to_attr="available_variants",
            ),
        )
        .order_by("-is_available", "-created_at", "-pk")
    )


def product_details() -> QuerySet[Product]:
    """Produtos visíveis com o que a página do produto usa: fotos e todas as variantes
    (inclusive as esgotadas, que aparecem riscadas), com tamanho e cor."""
    return (
        Product.objects.active()
        .select_related("category")
        .prefetch_related(
            "images",
            Prefetch("variants", queryset=ProductVariant.objects.select_related("size", "color")),
        )
    )


def filter_options(category: Category | None = None) -> tuple[list[Size], list[Color]]:
    """Tamanhos e cores com estoque entre os produtos visíveis (da categoria, se houver)."""
    products = Product.objects.active()
    if category is not None:
        products = products.filter(category=category)
    in_stock = ProductVariant.objects.filter(stock__gt=0, product__in=products)
    sizes = Size.objects.filter(Exists(in_stock.filter(size=OuterRef("pk"))))
    colors = Color.objects.filter(Exists(in_stock.filter(color=OuterRef("pk"))))
    return list(sizes), list(colors)


def categories_with_products() -> QuerySet[Category]:
    """Categorias ativas que têm pelo menos um produto visível."""
    visible = Product.objects.active().filter(category=OuterRef("pk"))
    return Category.objects.filter(is_active=True).filter(Exists(visible))
