from typing import Any
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.generic import DetailView, ListView

from apps.cart.cart import Cart

from . import selectors, services
from .models import Category, Product
from .presenters import CatalogFilters, ProductCard, ProductDetail


class ProductListView(ListView[Product]):
    """Listagem com filtros na querystring (`?categoria=<slug>&tamanho=<pk>&cor=<pk>`).

    Em requests do HTMX devolve só o bloco do catálogo (+ topo fora de banda e título).
    Ids de tamanho/cor que não estão entre as opções com estoque são ignorados.
    """

    template_name = "catalog/product_list.html"
    htmx_template = "catalog/partials/catalog_htmx.html"
    paginate_by = 12
    category: Category | None = None
    filters: CatalogFilters

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        patch_vary_headers(response, ["HX-Request"])
        return response

    def get_template_names(self) -> list[str]:
        return [self.htmx_template if _is_htmx(self.request) else self.template_name]

    def get_queryset(self) -> Any:
        slug = self.request.GET.get("categoria")
        if slug:
            self.category = get_object_or_404(Category, slug=slug, is_active=True)
        sizes, colors = selectors.filter_options(self.category)
        self.filters = CatalogFilters.build(
            category=self.category,
            sizes=sizes,
            colors=colors,
            size_id=_int_param(self.request.GET, "tamanho"),
            color_id=_int_param(self.request.GET, "cor"),
        )
        return selectors.catalog_products(
            category=self.category, size=self.filters.size, color=self.filters.color
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "catalogo"
        context["cards"] = [ProductCard.from_product(p) for p in context["object_list"]]
        context["categories"] = selectors.categories_with_products()
        context["current_category"] = self.category
        context["filters"] = self.filters
        if self.category is not None:
            context["meta_title"] = f"{self.category.name} — Tay Modas"
            # Filtros e página não entram no canônico: são variações da mesma lista.
            context["canonical_url"] = self.request.build_absolute_uri(
                f"{reverse('catalog:product_list')}?{urlencode({'categoria': self.category.slug})}"
            )
        context["show_hero"] = (
            self.category is None
            and not self.filters.is_active
            and not context["page_obj"].has_previous()
        )
        return context


class ProductDetailView(DetailView[Product]):
    """Página do produto. A escolha de tamanho/cor vem na querystring (`?tamanho=&cor=`);
    em requests do HTMX devolve só o formulário da peça.

    O botão "Adicionar à sacola" envia a escolha por POST. Completa, a peça entra na sacola:
    com HTMX volta o formulário com o aviso e o contador do topo (fora de banda); sem JS,
    redireciona para a página com `adicionado=1`. Incompleta, destaca o que falta e põe o foco
    no grupo pendente.
    """

    template_name = "catalog/product_detail.html"
    order_form_template = "catalog/partials/order_form.html"

    def get_queryset(self) -> Any:
        return selectors.product_details()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        response = self.render_to_response(self.get_context_data(object=self.object))
        patch_vary_headers(response, ["HX-Request"])
        return response

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        selection: services.VariantSelection = context["selection"]
        variant = selection.variant
        if variant is None:
            return self.render_to_response(context)

        Cart(request.session).add(variant.pk, stock=variant.stock)
        if not _is_htmx(request):
            query = urlencode(
                {"cor": variant.color_id, "tamanho": variant.size_id, "adicionado": 1}
            )
            return HttpResponseRedirect(f"{request.path}?{query}")
        context["added"] = True
        form = render_to_string(self.order_form_template, context, request=request)
        counter = render_to_string("partials/cart_link.html", {"oob": True}, request=request)
        return HttpResponse(form + counter)

    def get_template_names(self) -> list[str]:
        if _is_htmx(self.request):
            return [self.order_form_template]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "catalogo"
        product: Product = self.object
        params = self.request.POST if self.request.method == "POST" else self.request.GET
        selection = services.select_variant(
            list(product.variants.all()),
            size_id=_int_param(params, "tamanho"),
            color_id=_int_param(params, "cor"),
        )
        # Tentou adicionar sem escolher tudo: o aviso e o foco apontam o que falta.
        wants_order = self.request.method == "POST" and selection.variant is None
        detail = ProductDetail.from_product(product)
        context["detail"] = detail
        context["meta_title"] = f"{detail.name} — Tay Modas"
        context["meta_description"] = detail.description
        context["og_type"] = "product"
        if detail.images:
            context["meta_image"] = self.request.build_absolute_uri(detail.images[0].share_url)
        context["selection"] = selection
        context["added"] = selection.variant is not None and params.get("adicionado") == "1"
        context["wants_order"] = wants_order
        context["focus_group"], context["focus_choice"] = (
            _pending_choice(selection) if wants_order else ("", None)
        )
        context["is_sold_out"] = not any(v.is_in_stock for v in product.variants.all())
        return context


def _is_htmx(request: HttpRequest) -> bool:
    headers = request.headers
    # No restore de histórico o HTMX pede a página inteira, mesmo com HX-Request.
    return bool(headers.get("HX-Request")) and not headers.get("HX-History-Restore-Request")


def _int_param(params: QueryDict, name: str) -> int | None:
    value = params.get(name, "")
    return int(value) if value.isdecimal() else None


def _pending_choice(selection: services.VariantSelection) -> tuple[str, int | None]:
    """Grupo que falta escolher (cor antes de tamanho) e sua primeira opção disponível,
    que recebe o foco."""
    if selection.color is None:
        group, choices = "cor", selection.colors
    else:
        # Sem tamanho, ou combinação esgotada: o tamanho é o que precisa mudar.
        group, choices = "tamanho", selection.sizes
    first = next((choice for choice in choices if choice.is_available), None)
    return group, first.id if first else None
