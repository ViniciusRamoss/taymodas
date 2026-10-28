"""Sacola guardada na sessão da cliente: `{id da variação: quantidade}`. Sem login nem banco."""

from __future__ import annotations

from django.contrib.sessions.backends.base import SessionBase

SESSION_KEY = "sacola"


class Cart:
    def __init__(self, session: SessionBase) -> None:
        self.session = session

    @property
    def items(self) -> dict[int, int]:
        stored = self.session.get(SESSION_KEY, {})
        return {int(variant_id): quantity for variant_id, quantity in stored.items()}

    @property
    def count(self) -> int:
        return sum(self.items.values())

    def add(self, variant_id: int, *, stock: int) -> None:
        """Mais uma unidade, sem passar do estoque."""
        self.set(variant_id, self.items.get(variant_id, 0) + 1, stock=stock)

    def set(self, variant_id: int, quantity: int, *, stock: int) -> None:
        """Define a quantidade (limitada ao estoque); zero tira a peça da sacola."""
        items = self.items
        quantity = min(quantity, stock)
        if quantity > 0:
            items[variant_id] = quantity
        else:
            items.pop(variant_id, None)
        self._save(items)

    def remove(self, variant_id: int) -> None:
        items = self.items
        items.pop(variant_id, None)
        self._save(items)

    def replace(self, items: dict[int, int]) -> None:
        self._save(items)

    def clear(self) -> None:
        self.session.pop(SESSION_KEY, None)

    def _save(self, items: dict[int, int]) -> None:
        # Chaves em texto: a sessão é serializada em JSON.
        self.session[SESSION_KEY] = {str(variant_id): qty for variant_id, qty in items.items()}
