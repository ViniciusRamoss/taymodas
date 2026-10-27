from decimal import Decimal

import pytest

from apps.core.formatting import format_brl


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0.5"), "R$ 0,50"),
        (Decimal("99.9"), "R$ 99,90"),
        (Decimal("1234.56"), "R$ 1.234,56"),
        (Decimal("1000000"), "R$ 1.000.000,00"),
    ],
)
def test_format_brl(value: Decimal, expected: str) -> None:
    assert format_brl(value) == expected
