"""Cadastra as primeiras peças da loja a partir das fotos enviadas pela dona.

Nome, cor e preço vêm do nome de cada arquivo (ex.: "Conjunto de Renda Preto Price 160.jpeg").
Onde o arquivo não diz a cor, ela foi descrita a partir da foto. Tamanhos e estoque não vêm
nas fotos: entram os de `--sizes`/`--stock` e a dona corrige no painel.

Roda de novo sem duplicar: peças que já existem pelo nome são puladas.
"""

import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Color, Product, ProductImage, ProductVariant, Size


@dataclass(frozen=True)
class Photo:
    file_stem: str
    color: str


@dataclass(frozen=True)
class Item:
    name: str
    category: str
    price: str
    photos: tuple[Photo, ...]


ITEMS = (
    Item("Blusa Farm", "Blusas", "50", (Photo("Blusa Farm Price 50", "Estampada"),)),
    Item("Body Renda Branco", "Bodies", "60", (Photo("Body Renda Branco Price 60", "Branco"),)),
    Item(
        "Calça Alfaiataria Nude",
        "Calças",
        "100",
        (Photo("Calça Alfaiataria Nude Price 100", "Nude"),),
    ),
    Item("Calça Cargo", "Calças", "160", (Photo("Claça cargo Price 160", "Jeans"),)),
    Item(
        "Conjunto Alfaiataria Azul",
        "Conjuntos",
        "140",
        (Photo("Conjunto Alfaiataria Azul Price 140", "Azul"),),
    ),
    Item(
        "Conjunto Duna Azul", "Conjuntos", "140", (Photo("Conjunto Duna Azul Price 140", "Azul"),)
    ),
    Item(
        "Conjunto de Renda",
        "Conjuntos",
        "160",
        (
            Photo("Conjunto de Renda Preto Price 160", "Preto"),
            Photo("Conjunto de Renda Marrom Price 160", "Marrom"),
            Photo("Conjunto de Renda Azul Price 160", "Azul"),
        ),
    ),
    Item("Vestido Longo Azul", "Vestidos", "130", (Photo("Vestido longo Azul Price 130", "Azul"),)),
    Item(
        "Vestido Longo",
        "Vestidos",
        "130",
        (Photo("Vestido longo Price 130", "Preto com bolinhas"),),
    ),
)

# Bolinha da cor no site; cores sem tom único (estampa, bolinhas) aparecem só pelo nome.
COLOR_HEX = {
    "Preto": "#1f1b1d",
    "Branco": "#f7f5f0",
    "Marrom": "#4a3026",
    "Nude": "#d9c2a7",
    "Azul": "#7fa6cf",
    "Jeans": "#6f8fb5",
}


def _key(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


class Command(BaseCommand):
    help = "Cadastra as peças das fotos da loja (nome, categoria, cor, preço e foto)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("folder", type=Path, help="Pasta com as fotos.")
        parser.add_argument("--sizes", default="P,M,G", help="Tamanhos, separados por vírgula.")
        parser.add_argument("--stock", type=int, default=1, help="Estoque de cada combinação.")

    @transaction.atomic
    def handle(self, *args: Any, folder: Path, sizes: str, stock: int, **options: Any) -> None:
        files = {_key(path.stem): path for path in folder.glob("*") if path.is_file()}
        missing = [
            photo.file_stem
            for item in ITEMS
            for photo in item.photos
            if _key(photo.file_stem) not in files
        ]
        if missing:
            raise CommandError(f"Fotos não encontradas em {folder}: {', '.join(missing)}")

        size_objects = [
            Size.objects.get_or_create(name=name.strip(), defaults={"position": position})[0]
            for position, name in enumerate(sizes.split(","), start=1)
        ]
        created = 0
        for item in ITEMS:
            if Product.objects.filter(name=item.name).exists():
                self.stdout.write(f"Já existe, pulando: {item.name}")
                continue
            category, _ = Category.objects.get_or_create(name=item.category)
            product = Product.objects.create(
                name=item.name, category=category, price=Decimal(item.price)
            )
            for position, photo in enumerate(item.photos):
                color, _ = Color.objects.get_or_create(
                    name=photo.color, defaults={"hex_code": COLOR_HEX.get(photo.color, "")}
                )
                image = ProductImage(
                    product=product,
                    position=position,
                    alt_text=f"{item.name} na cor {photo.color.lower()}",
                )
                self._attach(image, files[_key(photo.file_stem)])
                for size in size_objects:
                    ProductVariant.objects.create(
                        product=product, size=size, color=color, stock=stock
                    )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} peça(s) cadastrada(s)."))

    def _attach(self, image: ProductImage, path: Path) -> None:
        """Com storage local, arquivo já dentro de MEDIA_ROOT é só referenciado (sem cópia);
        senão, é enviado ao storage (Cloudinary em produção)."""
        media_root = Path(settings.MEDIA_ROOT).resolve()
        resolved = path.resolve()
        is_local = isinstance(default_storage, FileSystemStorage)
        if is_local and resolved.is_relative_to(media_root):
            image.image.name = resolved.relative_to(media_root).as_posix()
            image.save()
            return
        with resolved.open("rb") as handle:
            image.image.save(path.name, File(handle), save=True)
