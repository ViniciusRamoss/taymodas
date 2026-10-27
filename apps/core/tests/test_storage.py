from unittest import mock

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.db.models.fields.files import FieldFile

from apps.core.images import image_url
from apps.core.storage import UPLOAD_TRANSFORMATION, CloudinaryMediaStorage


@pytest.fixture
def storage() -> CloudinaryMediaStorage:
    return CloudinaryMediaStorage()


def test_save_uploads_with_unique_public_id(storage: CloudinaryMediaStorage) -> None:
    with mock.patch("cloudinary.uploader.upload") as upload:
        upload.return_value = {"public_id": "products/2026/10/vestido-abc12345", "format": "jpg"}

        name = storage.save("products/2026/10/Vestido Novo.JPG", ContentFile(b"img"))

    assert name == "products/2026/10/vestido-abc12345.jpg"
    kwargs = upload.call_args.kwargs
    assert kwargs["public_id"].startswith("products/2026/10/vestido-novo-")
    assert kwargs["overwrite"] is False
    assert kwargs["transformation"] == UPLOAD_TRANSFORMATION


def test_exists_is_always_false(storage: CloudinaryMediaStorage) -> None:
    assert storage.exists("products/qualquer.jpg") is False


def test_delete_destroys_by_public_id(storage: CloudinaryMediaStorage) -> None:
    with mock.patch("cloudinary.uploader.destroy") as destroy:
        storage.delete("products/2026/10/vestido-abc.jpg")

    destroy.assert_called_once_with(
        "products/2026/10/vestido-abc", resource_type="image", invalidate=True
    )


def test_url_is_optimized_and_resizable(storage: CloudinaryMediaStorage) -> None:
    with mock.patch("cloudinary.utils.cloudinary_url", return_value=("https://x", {})) as build:
        assert storage.url("products/a.jpg", width=400) == "https://x"

    build.assert_called_once_with(
        "products/a",
        format="jpg",
        secure=True,
        fetch_format="auto",
        quality="auto",
        width=400,
        crop="limit",
    )


def test_url_of_empty_name_is_empty(storage: CloudinaryMediaStorage) -> None:
    assert storage.url("") == ""


def test_image_url_uses_cloudinary_resize(storage: CloudinaryMediaStorage) -> None:
    file = mock.Mock(spec=FieldFile, storage=storage)
    file.name = "products/a.jpg"
    file.__bool__ = lambda self: True

    with mock.patch.object(storage, "url", return_value="https://resized") as url:
        assert image_url(file, width=200) == "https://resized"

    url.assert_called_once_with("products/a.jpg", width=200)


def test_image_url_falls_back_to_plain_url() -> None:
    file = mock.Mock(spec=FieldFile, storage=InMemoryStorage(), url="/media/a.jpg")
    file.__bool__ = lambda self: True

    assert image_url(file, width=200) == "/media/a.jpg"


def test_image_url_of_empty_file_is_empty() -> None:
    assert image_url(None) == ""
