from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import pytest
from django.core.files.base import ContentFile

from apps.catalog.models import ProductImage

from .factories import ProductImageFactory

pytestmark = pytest.mark.django_db

CaptureCallbacks = Callable[..., AbstractContextManager[list[Callable[[], Any]]]]


def file_name(image: ProductImage) -> str:
    name = image.image.name
    assert name
    return name


def test_deleting_image_removes_file(django_capture_on_commit_callbacks: CaptureCallbacks) -> None:
    image = ProductImageFactory.create()
    storage, name = image.image.storage, file_name(image)
    assert storage.exists(name)

    with django_capture_on_commit_callbacks(execute=True):
        image.delete()

    assert not storage.exists(name)


def test_replacing_image_removes_old_file(
    django_capture_on_commit_callbacks: CaptureCallbacks,
) -> None:
    image = ProductImageFactory.create()
    storage, old_name = image.image.storage, file_name(image)

    with django_capture_on_commit_callbacks(execute=True):
        image.image.save("nova.png", ContentFile(b"nova"), save=True)

    assert not storage.exists(old_name)
    assert storage.exists(file_name(image))


def test_saving_without_changing_image_keeps_file(
    django_capture_on_commit_callbacks: CaptureCallbacks,
) -> None:
    image = ProductImageFactory.create()

    with django_capture_on_commit_callbacks(execute=True):
        image.alt_text = "Frente"
        image.save()

    assert image.image.storage.exists(file_name(image))
