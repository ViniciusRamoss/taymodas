from typing import Any

from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from . import selectors
from .models import Category, Product
from .presenters import ProductCard


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
