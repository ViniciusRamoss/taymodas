"""Storage de mídia no Cloudinary usando o SDK oficial.

Ativado em `config.settings.base` quando `CLOUDINARY_URL` está definido. O nome salvo no
banco é `<public_id>.<formato>`, ex.: `products/2026/10/vestido-1a2b3c4d.jpg`.
"""

from __future__ import annotations

import posixpath
import uuid
from typing import Any

import cloudinary.uploader
import cloudinary.utils
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify

# Reduz fotos muito grandes já no upload para economizar a cota gratuita.
UPLOAD_TRANSFORMATION = [{"width": 2000, "height": 2000, "crop": "limit"}]


def split_name(name: str) -> tuple[str, str]:
    """Separa `pasta/arquivo.jpg` em (`pasta/arquivo`, `jpg`)."""
    public_id, ext = posixpath.splitext(name)
    return public_id, ext.lstrip(".")


@deconstructible
class CloudinaryMediaStorage(Storage):
    def _save(self, name: str, content: File[Any]) -> str:
        directory, filename = posixpath.split(name.replace("\\", "/"))
        stem = slugify(posixpath.splitext(filename)[0]) or "foto"
        public_id = posixpath.join(directory, f"{stem}-{uuid.uuid4().hex[:8]}")
        content.seek(0)
        result = cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
            transformation=UPLOAD_TRANSFORMATION,
        )
        return f"{result['public_id']}.{result['format']}"

    def exists(self, name: str) -> bool:
        # Nomes recebem sufixo aleatório no `_save`, então nunca colidem.
        return False

    def delete(self, name: str) -> None:
        public_id, _ = split_name(name)
        cloudinary.uploader.destroy(public_id, resource_type="image", invalidate=True)

    def url(self, name: str | None, *, width: int | None = None) -> str:
        if not name:
            return ""
        public_id, ext = split_name(name)
        options: dict[str, Any] = {"secure": True, "fetch_format": "auto", "quality": "auto"}
        if width:
            options.update(width=width, crop="limit")
        url: str = cloudinary.utils.cloudinary_url(public_id, format=ext or None, **options)[0]
        return url
