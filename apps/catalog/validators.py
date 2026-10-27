from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb: int) -> None:
        self.max_mb = max_mb

    def __call__(self, file: File[Any]) -> None:
        if file.size is not None and file.size > self.max_mb * 1024 * 1024:
            raise ValidationError(
                f"A foto tem mais de {self.max_mb} MB. Envie uma versão menor "
                "(no celular, compartilhe pelo WhatsApp para si mesma e salve de novo).",
                code="file_too_large",
            )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MaxFileSizeValidator) and other.max_mb == self.max_mb

    def __hash__(self) -> int:
        return hash(self.max_mb)


validate_image_size = MaxFileSizeValidator(max_mb=10)
