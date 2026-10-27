from django.http import HttpRequest

from .models import StoreSettings


def store(request: HttpRequest) -> dict[str, StoreSettings]:
    """Disponibiliza as configurações da loja (`store`) em todos os templates."""
    return {"store": StoreSettings.load()}


def seo(request: HttpRequest) -> dict[str, str]:
    """URL canônica padrão (sem querystring). Views podem sobrescrever `canonical_url`."""
    return {"canonical_url": request.build_absolute_uri(request.path)}
