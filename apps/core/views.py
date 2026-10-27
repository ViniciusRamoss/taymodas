from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET


@require_GET
def healthcheck(request: HttpRequest) -> JsonResponse:
    """Usado pela hospedagem para saber se o app e o banco estão de pé."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:
    """Libera o catálogo e aponta o sitemap. Combinações de filtro e páginas da lista não são
    rastreadas (viram milhares de URLs da mesma lista). O admin fica de fora por não estar
    linkado; listá-lo aqui revelaria o endereço secreto."""
    lines = [
        "User-agent: *",
        "Disallow: /*?*tamanho=",
        "Disallow: /*?*cor=",
        "Disallow: /*?*page=",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
