from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.text import unique_slugify

from .validators import validate_image_size

HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Use o formato #RRGGBB, por exemplo #000000 para preto.",
)


class Category(models.Model):
    name = models.CharField("nome", max_length=60, unique=True)
    slug = models.SlugField(
        "endereço na web",
        max_length=70,
        unique=True,
        blank=True,
        help_text="Preenchido automaticamente a partir do nome.",
    )
    position = models.PositiveSmallIntegerField(
        "ordem",
        default=0,
        help_text="Categorias com número menor aparecem primeiro no site.",
    )
    is_active = models.BooleanField(
        "visível no site",
        default=True,
        help_text="Desmarque para esconder a categoria sem apagá-la.",
    )

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Size(models.Model):
    name = models.CharField(
        "tamanho",
        max_length=20,
        unique=True,
        help_text="Ex.: P, M, G ou 38. Cadastre uma vez e reutilize em todos os produtos.",
    )
    position = models.PositiveSmallIntegerField(
        "ordem",
        default=0,
        help_text="Define a ordem de exibição (ex.: P=1, M=2, G=3).",
    )

    class Meta:
        verbose_name = "tamanho"
        verbose_name_plural = "tamanhos"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class Color(models.Model):
    name = models.CharField(
        "cor",
        max_length=40,
        unique=True,
        help_text="Ex.: Preto, Off-white. Cadastre uma vez e reutilize em todos os produtos.",
    )
    hex_code = models.CharField(
        "código da cor",
        max_length=7,
        blank=True,
        validators=[HEX_COLOR_VALIDATOR],
        help_text="Opcional. Mostra uma bolinha com a cor no site (ex.: #000000).",
    )

    class Meta:
        verbose_name = "cor"
        verbose_name_plural = "cores"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ProductQuerySet(models.QuerySet["Product"]):
    def active(self) -> ProductQuerySet:
        """Produtos visíveis no site: ativos e de categoria ativa."""
        return self.filter(is_active=True, category__is_active=True)

    def in_stock(self) -> ProductQuerySet:
        """Produtos com pelo menos uma variante com estoque."""
        return self.filter(models.Exists(self._variants_in_stock()))

    def on_sale(self, day: date | None = None) -> ProductQuerySet:
        """Produtos com preço promocional valendo em `day` (padrão: hoje)."""
        day = day or timezone.localdate()
        return self.filter(sale_price__isnull=False).filter(
            models.Q(sale_ends_at__isnull=True) | models.Q(sale_ends_at__gte=day)
        )

    def sold_out(self) -> ProductQuerySet:
        """Produtos sem nenhuma variante com estoque (inclui os sem variantes)."""
        return self.exclude(models.Exists(self._variants_in_stock()))

    def _variants_in_stock(self) -> models.QuerySet[ProductVariant]:
        return ProductVariant.objects.filter(product=models.OuterRef("pk"), stock__gt=0)

    def with_total_stock(self) -> ProductQuerySet:
        """Anota `total_stock` com a soma do estoque de todas as variantes.

        Usa subquery em vez de `Sum("variants__stock")` para o valor não ser multiplicado
        quando o queryset também filtra por variantes (ex.: filtro de tamanho no admin).
        """
        per_product = (
            ProductVariant.objects.filter(product=models.OuterRef("pk"))
            .values("product")
            .annotate(total=models.Sum("stock"))
            .values("total")
        )
        return self.annotate(
            total_stock=Coalesce(
                models.Subquery(per_product, output_field=models.IntegerField()), 0
            )
        )


class Product(TimeStampedModel):
    name = models.CharField("nome", max_length=120)
    slug = models.SlugField(
        "endereço na web",
        max_length=140,
        unique=True,
        blank=True,
        help_text="Preenchido automaticamente a partir do nome.",
    )
    description = models.TextField(
        "descrição",
        blank=True,
        help_text="Tecido, caimento, medidas, dicas de uso...",
    )
    price = models.DecimalField(
        "preço (R$)",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    sale_price = models.DecimalField(
        "preço promocional (R$)",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=(
            "Opcional. Preencha para colocar a peça em promoção: o preço normal aparece riscado. "
            "Apague para encerrar a promoção."
        ),
    )
    sale_ends_at = models.DateField(
        "promoção até",
        null=True,
        blank=True,
        help_text=(
            "Opcional. Último dia da promoção; no dia seguinte volta o preço normal sozinho. "
            "Vazio: vale até você apagar o preço promocional."
        ),
    )
    category = models.ForeignKey(
        Category,
        verbose_name="categoria",
        on_delete=models.PROTECT,
        related_name="products",
    )
    is_active = models.BooleanField(
        "visível no site",
        default=True,
        help_text="Desmarque para esconder o produto sem apagá-lo.",
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    def clean(self) -> None:
        if self.sale_price is not None and self.price is not None and self.sale_price >= self.price:
            raise ValidationError(
                {"sale_price": "O preço promocional precisa ser menor que o preço normal."}
            )
        if self.sale_ends_at is not None and self.sale_price is None:
            raise ValidationError(
                {"sale_ends_at": "Preencha o preço promocional ou deixe esta data vazia."}
            )

    def is_on_sale(self, day: date | None = None) -> bool:
        if self.sale_price is None:
            return False
        return self.sale_ends_at is None or self.sale_ends_at >= (day or timezone.localdate())

    def current_price(self, day: date | None = None) -> Decimal:
        """Preço que a cliente paga hoje: o promocional, se a promoção está valendo."""
        if self.is_on_sale(day) and self.sale_price is not None:
            return self.sale_price
        return self.price


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="produto",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        "foto",
        upload_to="products/%Y/%m/",
        validators=[validate_image_size],
        help_text="JPG, PNG ou WEBP, até 10 MB. Fotos em pé (retrato) ficam melhores no site.",
    )
    alt_text = models.CharField(
        "descrição da foto",
        max_length=150,
        blank=True,
        help_text="Opcional. Ajuda pessoas com deficiência visual (ex.: vestido preto de frente).",
    )
    position = models.PositiveSmallIntegerField(
        "ordem",
        default=0,
        help_text="A foto com o menor número é a capa do produto.",
    )

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Foto {self.position} de {self.product}"


class ProductVariant(models.Model):
    """Combinação vendável de tamanho + cor de um produto, com seu estoque."""

    product = models.ForeignKey(
        Product,
        verbose_name="produto",
        on_delete=models.CASCADE,
        related_name="variants",
    )
    size = models.ForeignKey(
        Size,
        verbose_name="tamanho",
        on_delete=models.PROTECT,
        related_name="variants",
    )
    color = models.ForeignKey(
        Color,
        verbose_name="cor",
        on_delete=models.PROTECT,
        related_name="variants",
    )
    stock = models.PositiveIntegerField(
        "estoque",
        default=0,
        help_text="Quantidade disponível. Atualize depois de cada venda.",
    )

    class Meta:
        verbose_name = "variação (tamanho e cor)"
        verbose_name_plural = "variações (tamanho e cor)"
        ordering = ["size__position", "size__name", "color__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "size", "color"],
                name="unique_variant_per_product",
                violation_error_message="Este produto já tem essa combinação de tamanho e cor.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.size} / {self.color}"

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0
