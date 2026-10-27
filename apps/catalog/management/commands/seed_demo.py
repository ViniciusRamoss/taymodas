"""Cria produtos de demonstração para desenvolvimento e screenshots.

Todos os dados são fictícios e marcados como "Demo"; nada aqui representa a loja real.
"""

import io
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from apps.catalog.models import Category, Color, Product, ProductImage, ProductVariant, Size

DEMO_CATEGORY = "Demo"
SIZES = [("P", 1), ("M", 2), ("G", 3)]
COLORS = [("Preto demo", "#000000"), ("Off-white demo", "#efeae0"), ("Vinho demo", "#6d1f2e")]
# Tons usados para gerar fotos lisas no lugar de fotos reais.
PHOTO_TONES = ["#d9cbbb", "#2f2f2f", "#a14d4d", "#c2b59b", "#55606b", "#e6dfd3"]


def solid_photo(hex_color: str) -> ContentFile[bytes]:
    buffer = io.BytesIO()
    Image.new("RGB", (600, 800), hex_color).save(buffer, format="JPEG", quality=80)
    return ContentFile(buffer.getvalue(), name="demo.jpg")


class Command(BaseCommand):
    help = "Cria produtos fictícios de demonstração (somente com DEBUG=True)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--count", type=int, default=10)

    @transaction.atomic
    def handle(self, *args: Any, count: int, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("seed_demo só roda em desenvolvimento (DEBUG=True).")

        category, _ = Category.objects.get_or_create(name=DEMO_CATEGORY)
        sizes = [Size.objects.get_or_create(name=n, defaults={"position": p})[0] for n, p in SIZES]
        colors = [
            Color.objects.get_or_create(name=n, defaults={"hex_code": h})[0] for n, h in COLORS
        ]

        for index in range(count):
            product = Product.objects.create(
                name=f"Peça demo {index + 1}",
                description="Produto fictício para demonstração.",
                price=Decimal("50.00") + Decimal(index * 10),
                category=category,
            )
            ProductImage.objects.create(
                product=product, image=solid_photo(PHOTO_TONES[index % len(PHOTO_TONES)])
            )
            # A cada 4 peças, uma fica esgotada para mostrar o selo.
            stock = 0 if index % 4 == 3 else 2
            for size in sizes[: 1 + index % 3]:
                for color in colors[: 1 + index % 2]:
                    ProductVariant.objects.create(
                        product=product, size=size, color=color, stock=stock
                    )

        self.stdout.write(self.style.SUCCESS(f"{count} produtos de demonstração criados."))
