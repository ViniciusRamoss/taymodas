from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.catalog.models import Product, ProductVariant
from apps.core.formatting import format_brl
from apps.core.models import StoreSettings

from . import services
from .cart import Cart


class CartView(TemplateView):
    """Sacola da cliente: peças, quantidades, total e o botão que envia tudo pelo WhatsApp."""

    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request.session)
        items = cart.items
        lines = services.build_lines(items, services.cart_variants(items))
        # Peças que saíram do site ou esgotaram aparecem só desta vez; a sacola (e o
        # contador do topo) passa a ter só o que dá para pedir.
        available = {line.variant_id: line.quantity for line in lines if line.is_available}
        if available != items:
            cart.replace(available)
        context["nav_current"] = "sacola"
        context["meta_title"] = "Sacola — Tay Modas"
        context["lines"] = lines
        context["total"] = format_brl(services.cart_total(lines))
        context["has_sold_out"] = any(not line.is_available for line in lines)
        context["order_url"] = services.build_whatsapp_cart_url(
            lines, StoreSettings.load(), self.request.build_absolute_uri
        )
        return context


@require_POST
def update(request: HttpRequest, variant_id: int) -> HttpResponse:
    """Muda a quantidade de uma peça (`quantidade`; zero ou vazio tira da sacola)."""
    cart = Cart(request.session)
    quantity = request.POST.get("quantidade", "")
    if quantity.isdecimal() and int(quantity) > 0:
        variant = get_object_or_404(
            ProductVariant, pk=variant_id, product__in=Product.objects.active()
        )
        cart.set(variant_id, int(quantity), stock=variant.stock)
    else:
        cart.remove(variant_id)
    return HttpResponseRedirect(reverse("cart:detail"))


@require_POST
def clear(request: HttpRequest) -> HttpResponse:
    Cart(request.session).clear()
    return HttpResponseRedirect(reverse("cart:detail"))
