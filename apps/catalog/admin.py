from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString

from apps.core.formatting import format_brl
from apps.core.images import image_url

from .models import Category, Color, Product, ProductImage, ProductVariant, Size

THUMBNAIL_WIDTH = 120


def thumbnail(image: ProductImage | None, size: int = 60) -> SafeString | str:
    if not image or not image.image:
        return "—"
    return format_html(
        '<img src="{}" alt="" width="{}" height="{}" style="object-fit:cover;border-radius:6px;">',
        image_url(image.image, width=THUMBNAIL_WIDTH),
        size,
        round(size * 4 / 3),
    )


def stock_badge(stock: int) -> SafeString:
    if stock > 0:
        return format_html("<strong>{}</strong>", stock)
    return format_html('<span style="color:#b91c1c;font-weight:600;">{}</span>', "Esgotado")


class ProductImageInline(admin.TabularInline[ProductImage, Product]):
    model = ProductImage
    extra = 1
    fields = ["preview", "image", "alt_text", "position"]
    readonly_fields = ["preview"]
    verbose_name = "foto"
    verbose_name_plural = "Fotos (a de menor ordem é a capa)"

    @admin.display(description="prévia")
    def preview(self, obj: ProductImage) -> SafeString | str:
        return thumbnail(obj, size=80)


class ProductVariantInline(admin.TabularInline[ProductVariant, Product]):
    model = ProductVariant
    extra = 1
    fields = ["size", "color", "stock"]
    verbose_name = "tamanho e cor"
    verbose_name_plural = "Tamanhos, cores e estoque"


class StockStatusFilter(admin.SimpleListFilter):
    title = "estoque"
    parameter_name = "estoque"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin[Product]
    ) -> list[tuple[str, str]]:
        return [("disponivel", "Com estoque"), ("esgotado", "Esgotado")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Product]) -> QuerySet[Product]:
        if self.value() == "disponivel":
            return queryset.in_stock()  # type: ignore[attr-defined, no-any-return]
        if self.value() == "esgotado":
            return queryset.sold_out()  # type: ignore[attr-defined, no-any-return]
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin[Product]):
    list_display = ["cover", "name", "category", "formatted_price", "stock", "is_active"]
    list_display_links = ["cover", "name"]
    list_editable = ["is_active"]
    list_filter = [StockStatusFilter, "is_active", "category", "variants__size", "variants__color"]
    search_fields = ["name", "description"]
    search_help_text = "Busque pelo nome ou descrição do produto."
    list_per_page = 30
    save_on_top = True
    actions = ["make_active", "make_inactive"]
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ["slug", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["name", "category", "price", "description", "is_active"]}),
        (
            "Informações automáticas",
            {"fields": ["slug", "created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Product]:
        queryset: QuerySet[Product] = (
            super()
            .get_queryset(request)
            .with_total_stock()  # type: ignore[attr-defined]
            .select_related("category")
            .prefetch_related("images")
        )
        return queryset

    def get_fieldsets(self, request: HttpRequest, obj: Product | None = None) -> Any:
        # No cadastro novo os campos automáticos ainda estão vazios; mostrar só confunde.
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets[:1] if obj is None else fieldsets

    @admin.display(description="foto")
    def cover(self, obj: Product) -> SafeString | str:
        # `images.all()` usa o prefetch; `.first()` faria uma query por linha.
        images = list(obj.images.all())
        return thumbnail(images[0] if images else None)

    @admin.display(description="preço", ordering="price")
    def formatted_price(self, obj: Product) -> str:
        return format_brl(obj.price)

    @admin.display(description="estoque total", ordering="total_stock")
    def stock(self, obj: Product) -> SafeString:
        return stock_badge(obj.total_stock)  # type: ignore[attr-defined]

    @admin.action(description="Mostrar no site os produtos selecionados")
    def make_active(self, request: HttpRequest, queryset: QuerySet[Product]) -> None:
        updated = Product.objects.filter(pk__in=queryset.values("pk")).update(is_active=True)
        self.message_user(
            request, f"{updated} produto(s) agora aparecem no site.", messages.SUCCESS
        )

    @admin.action(description="Esconder do site os produtos selecionados")
    def make_inactive(self, request: HttpRequest, queryset: QuerySet[Product]) -> None:
        updated = Product.objects.filter(pk__in=queryset.values("pk")).update(is_active=False)
        self.message_user(request, f"{updated} produto(s) escondidos do site.", messages.SUCCESS)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin[ProductVariant]):
    """Atalho para atualizar estoque de vários produtos de uma vez."""

    list_display = ["product", "size", "color", "stock", "status"]
    list_editable = ["stock"]
    list_filter = ["product__category", "size", "color"]
    search_fields = ["product__name"]
    search_help_text = "Busque pelo nome do produto."
    list_select_related = ["product", "size", "color"]
    list_per_page = 50
    autocomplete_fields = ["product"]

    @admin.display(description="situação", ordering="stock")
    def status(self, obj: ProductVariant) -> SafeString:
        return stock_badge(obj.stock)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin[Category]):
    list_display = ["name", "position", "is_active", "product_count"]
    list_editable = ["position", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["slug"]
    fields = ["name", "position", "is_active", "slug"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="produtos", ordering="product_count")
    def product_count(self, obj: Category) -> int:
        count: int = obj.product_count  # type: ignore[attr-defined]
        return count


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin[Size]):
    list_display = ["name", "position"]
    list_editable = ["position"]
    search_fields = ["name"]


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin[Color]):
    list_display = ["swatch", "name", "hex_code"]
    list_display_links = ["swatch", "name"]
    search_fields = ["name"]

    @admin.display(description="")
    def swatch(self, obj: Color) -> SafeString | str:
        if not obj.hex_code:
            return "—"
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;border-radius:50%;'
            'background:{};border:1px solid #ccc;"></span>',
            obj.hex_code,
        )
