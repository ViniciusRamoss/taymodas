from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.cache import patch_vary_headers
from django.views.generic import DetailView, ListView

from apps.core.models import StoreSettings

from . import selectors, services
from .models import Category, Product
from .presenters import ProductCard, ProductDetail


class ProductListView(ListView[Product]):
    template_name = "catalog/product_list.html"
    paginate_by = 12
    category: Category | None = None

    def get_queryset(self) -> Any:
        slug = self.request.GET.get("categoria")
        if slug:
            self.category = get_object_or_404(Category, slug=slug, is_active=True)
        return selectors.catalog_products(category=self.category)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["cards"] = [ProductCard.from_product(p) for p in context["object_list"]]
        context["categories"] = selectors.categories_with_products()
        context["current_category"] = self.category
        return context


class ProductDetailView(DetailView[Product]):
    """Página do produto. A escolha de tamanho/cor vem na querystring (`?tamanho=&cor=`);
    em requests do HTMX devolve só o formulário de pedido."""

    template_name = "catalog/product_detail.html"
    order_form_template = "catalog/partials/order_form.html"

    def get_queryset(self) -> Any:
        return selectors.product_details()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        patch_vary_headers(response, ["HX-Request"])
        return response

    def get_template_names(self) -> list[str]:
        headers = self.request.headers
        # No restore de histórico o HTMX pede a página inteira, mesmo com HX-Request.
        if headers.get("HX-Request") and not headers.get("HX-History-Restore-Request"):
            return [self.order_form_template]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product: Product = self.object
        selection = services.select_variant(
            list(product.variants.all()),
            size_id=self._int_param("tamanho"),
            color_id=self._int_param("cor"),
        )
        order_url = None
        if selection.variant is not None:
            order_url = services.build_whatsapp_order_url(
                selection.variant,
                StoreSettings.load(),
                self.request.build_absolute_uri(product.get_absolute_url()),
            )
        context["detail"] = ProductDetail.from_product(product)
        context["selection"] = selection
        context["order_url"] = order_url
        context["is_sold_out"] = not any(v.is_in_stock for v in product.variants.all())
        return context

    def _int_param(self, name: str) -> int | None:
        value = self.request.GET.get(name, "")
        return int(value) if value.isdecimal() else None
