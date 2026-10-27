from decimal import Decimal


def format_brl(value: Decimal) -> str:
    """Formata um valor em reais: `Decimal("1234.5")` vira `"R$ 1.234,50"`."""
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"
