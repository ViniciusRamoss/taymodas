import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from apps.catalog.validators import MaxFileSizeValidator


def test_accepts_file_up_to_limit() -> None:
    MaxFileSizeValidator(max_mb=1)(ContentFile(b"x" * 1024 * 1024))


def test_rejects_file_over_limit() -> None:
    with pytest.raises(ValidationError, match="mais de 1 MB"):
        MaxFileSizeValidator(max_mb=1)(ContentFile(b"x" * (1024 * 1024 + 1)))


def test_validators_with_same_limit_are_equal() -> None:
    assert MaxFileSizeValidator(2) == MaxFileSizeValidator(2)
    assert MaxFileSizeValidator(2) != MaxFileSizeValidator(3)
    assert hash(MaxFileSizeValidator(2)) == hash(MaxFileSizeValidator(2))
