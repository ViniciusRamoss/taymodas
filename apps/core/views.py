from typing import Any

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from .models import StoreSettings


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


DELIVERY_QUESTION = "Olá! Quero consultar a entrega para o meu endereço."
CHAT_GREETING = "Olá! Vim pelo site da Tay Modas."


class DeliveryView(TemplateView):
    template_name = "core/delivery.html"
    extra_context = {
        "meta_title": "Entregas — Tay Modas",
        "meta_description": (
            "Envio para todo o Brasil e entrega por mototáxi em Ribeirão Preto e região. "
            "Veja as cidades atendidas e onde fica a loja em Serrana-SP."
        ),
        "nav_current": "entregas",
    }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["whatsapp_url"] = StoreSettings.load().whatsapp_url(DELIVERY_QUESTION)
        return context


class HowToBuyView(TemplateView):
    template_name = "core/how_to_buy.html"
    extra_context = {
        "meta_title": "Como comprar — Tay Modas",
        "meta_description": (
            "Escolha a peça, o tamanho e a cor no site e finalize o pedido pelo WhatsApp com a "
            "mensagem já pronta."
        ),
        "nav_current": "como-comprar",
    }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["whatsapp_url"] = StoreSettings.load().whatsapp_url(CHAT_GREETING)
        return context
