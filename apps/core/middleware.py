from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control


class RevalidateHtmlMiddleware:
    """Páginas HTML sem `Cache-Control` passam a revalidar (`no-cache`) a cada visita.

    O CSS tem nome com hash (manifest do WhiteNoise) e o nome antigo some a cada deploy. Sem
    este cabeçalho o Safari reaproveita o HTML guardado, pede o CSS antigo, recebe 404 e mostra
    a página sem estilo.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        is_html = response.get("Content-Type", "").startswith("text/html")
        if is_html and not response.has_header("Cache-Control"):
            patch_cache_control(response, no_cache=True)
        return response
