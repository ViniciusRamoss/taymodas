"""Comando que cadastra as peças a partir das fotos da loja."""

import io
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from PIL import Image

from apps.catalog.management.commands.import_store_photos import ITEMS
from apps.catalog.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def write_photos(folder: Path) -> None:
    for item in ITEMS:
        for photo in item.photos:
            buffer = io.BytesIO()
            Image.new("RGB", (30, 40), "#c0a0b0").save(buffer, format="JPEG")
            (folder / f"{photo.file_stem}.jpeg").write_bytes(buffer.getvalue())


def test_imports_every_item_once(tmp_path: Path) -> None:
    write_photos(tmp_path)

    call_command("import_store_photos", str(tmp_path), "--sizes", "P,M", stdout=io.StringIO())
    call_command("import_store_photos", str(tmp_path), stdout=io.StringIO())

    assert Product.objects.count() == len(ITEMS)
    lace = Product.objects.get(name="Conjunto de Renda")
    assert lace.price == 160
    assert lace.category.name == "Conjuntos"
    assert list(lace.images.values_list("position", flat=True)) == [0, 1, 2]
    assert ProductVariant.objects.filter(product=lace).count() == 6  # 3 cores x 2 tamanhos
    assert Product.objects.filter(name="Calça Cargo").exists()  # arquivo "Claça cargo"


def test_missing_photo_stops_before_writing(tmp_path: Path) -> None:
    write_photos(tmp_path)
    (tmp_path / "Blusa Farm Price 50.jpeg").unlink()

    with pytest.raises(CommandError, match="Blusa Farm Price 50"):
        call_command("import_store_photos", str(tmp_path), stdout=io.StringIO())
    assert not Product.objects.exists()
