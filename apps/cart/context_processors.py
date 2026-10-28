from django.http import HttpRequest

from .cart import Cart


def cart(request: HttpRequest) -> dict[str, int]:
    """Quantidade de peças na sacola (`cart_count`), para o contador do topo."""
    return {"cart_count": Cart(request.session).count}
