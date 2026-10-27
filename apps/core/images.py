from django.db.models.fields.files import FieldFile

from .storage import CloudinaryMediaStorage


def image_url(file: FieldFile | None, width: int | None = None) -> str:
    """URL da imagem, redimensionada pelo Cloudinary quando ele é o storage.

    Em dev/testes (storage local) devolve a URL original; o navegador redimensiona.
    """
    if not file:
        return ""
    if width and isinstance(file.storage, CloudinaryMediaStorage):
        return file.storage.url(file.name, width=width)
    return file.url
