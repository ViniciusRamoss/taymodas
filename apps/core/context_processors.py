from django.http import HttpRequest

from .models import StoreSettings


def store(request: HttpRequest) -> dict[str, StoreSettings]:
    """Disponibiliza as configurações da loja (`store`) em todos os templates."""
    return {"store": StoreSettings.load()}
