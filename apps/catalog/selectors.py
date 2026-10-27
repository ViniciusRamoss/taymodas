"""Consultas de leitura do catálogo público, já otimizadas para os templates."""

from django.db.models import Exists, OuterRef, Prefetch, QuerySet

from .models import Category, Product, ProductVariant


def catalog_products(category: Category | None = None) -> QuerySet[Product]:
    """Produtos visíveis, com estoque primeiro e mais novos antes.

    Cada produto vem com `is_available` anotado e `available_variants` (só variantes com
    estoque, com tamanho e cor) pré-carregado, para a listagem não fazer query por item.
    """
    products = Product.objects.active()
    if category is not None:
        products = products.filter(category=category)

    in_stock = ProductVariant.objects.filter(stock__gt=0)
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


def categories_with_products() -> QuerySet[Category]:
    """Categorias ativas que têm pelo menos um produto visível."""
    visible = Product.objects.active().filter(category=OuterRef("pk"))
    return Category.objects.filter(is_active=True).filter(Exists(visible))
