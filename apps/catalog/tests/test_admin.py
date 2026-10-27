import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from PIL import Image

from apps.catalog.models import Product, ProductVariant
from apps.core.models import StoreSettings

from .factories import (
    CategoryFactory,
    ColorFactory,
    ProductFactory,
    ProductImageFactory,
    ProductVariantFactory,
    SizeFactory,
)

pytestmark = pytest.mark.django_db


def png_upload(name: str = "foto.png") -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (30, 40), "black").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def inline_management(prefix: str, total: int, initial: int = 0) -> dict[str, str]:
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


@pytest.mark.parametrize("model", ["product", "productvariant", "category", "size", "color"])
def test_changelists_render(admin_client: Client, model: str) -> None:
    variant = ProductVariantFactory.create()
    ProductImageFactory.create(product=variant.product)

    response = admin_client.get(reverse(f"admin:catalog_{model}_changelist"))

    assert response.status_code == 200


def test_product_changelist_shows_price_in_reais_and_sold_out(admin_client: Client) -> None:
    ProductFactory.create(name="Vestido Sem Estoque", price="1234.50")

    content = admin_client.get(reverse("admin:catalog_product_changelist")).content.decode()

    assert "R$ 1.234,50" in content
    assert "Esgotado" in content


@pytest.mark.parametrize(("value", "expected"), [("disponivel", "Com"), ("esgotado", "Sem")])
def test_product_stock_filter(admin_client: Client, value: str, expected: str) -> None:
    ProductVariantFactory.create(product=ProductFactory.create(name="Com"), stock=1)
    ProductFactory.create(name="Sem")

    response = admin_client.get(reverse("admin:catalog_product_changelist"), {"estoque": value})

    assert [p.name for p in response.context["cl"].result_list] == [expected]


def test_product_search(admin_client: Client) -> None:
    ProductFactory.create(name="Vestido Floral")
    ProductFactory.create(name="Calça Jeans")

    response = admin_client.get(reverse("admin:catalog_product_changelist"), {"q": "floral"})

    assert [p.name for p in response.context["cl"].result_list] == ["Vestido Floral"]


def test_add_form_hides_automatic_fields(admin_client: Client) -> None:
    response = admin_client.get(reverse("admin:catalog_product_add"))

    assert response.status_code == 200
    assert "Informações automáticas" not in response.content.decode()


def test_change_form_shows_photo_preview(admin_client: Client) -> None:
    image = ProductImageFactory.create()

    response = admin_client.get(reverse("admin:catalog_product_change", args=[image.product.pk]))

    content = response.content.decode()
    assert "Informações automáticas" in content
    assert image.image.url in content


def test_create_product_with_photo_and_variant_inline(admin_client: Client) -> None:
    category = CategoryFactory.create()
    size = SizeFactory.create(name="M")
    color = ColorFactory.create(name="Preto")
    data = {
        "name": "Vestido Midi",
        "category": category.pk,
        "price": "149.90",
        "description": "Viscose.",
        "is_active": "on",
        **inline_management("images", total=1),
        "images-0-image": png_upload(),
        "images-0-alt_text": "Frente",
        "images-0-position": "0",
        **inline_management("variants", total=1),
        "variants-0-size": size.pk,
        "variants-0-color": color.pk,
        "variants-0-stock": "2",
    }

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 302
    product = Product.objects.get()
    assert product.slug == "vestido-midi"
    assert product.images.count() == 1
    assert str(product.variants.get()) == "M / Preto"


def test_duplicate_variant_inline_is_rejected(admin_client: Client) -> None:
    category = CategoryFactory.create()
    size, color = SizeFactory.create(), ColorFactory.create()
    row = {"size": size.pk, "color": color.pk, "stock": "1"}
    data = {
        "name": "Saia",
        "category": category.pk,
        "price": "80",
        **inline_management("images", total=0),
        **inline_management("variants", total=2),
        **{f"variants-0-{key}": value for key, value in row.items()},
        **{f"variants-1-{key}": value for key, value in row.items()},
    }

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 200
    assert not Product.objects.exists()


@pytest.mark.parametrize(("action", "expected"), [("make_active", True), ("make_inactive", False)])
def test_bulk_visibility_actions(admin_client: Client, action: str, expected: bool) -> None:
    products = ProductFactory.create_batch(2, is_active=not expected)

    admin_client.post(
        reverse("admin:catalog_product_changelist"),
        {"action": action, "_selected_action": [p.pk for p in products]},
    )

    assert set(Product.objects.values_list("is_active", flat=True)) == {expected}


def test_stock_is_editable_from_variant_list(admin_client: Client) -> None:
    variant = ProductVariantFactory.create(stock=5)
    data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-id": str(variant.pk),
        "form-0-stock": "3",
        "_save": "Salvar",
    }

    response = admin_client.post(reverse("admin:catalog_productvariant_changelist"), data)

    assert response.status_code == 302
    assert ProductVariant.objects.get().stock == 3


def test_category_list_counts_products(admin_client: Client) -> None:
    category = CategoryFactory.create()
    ProductFactory.create_batch(3, category=category)

    response = admin_client.get(reverse("admin:catalog_category_changelist"))

    assert response.context["cl"].result_list[0].product_count == 3


def test_color_list_shows_swatch_only_with_hex(admin_client: Client) -> None:
    ColorFactory.create(name="Dourado", hex_code="#d4af37")
    ColorFactory.create(name="Estampado", hex_code="")

    content = admin_client.get(reverse("admin:catalog_color_changelist")).content.decode()

    assert "background:#d4af37" in content


def test_groups_are_hidden_from_admin(admin_client: Client) -> None:
    response = admin_client.get(reverse("admin:index"))

    assert "Grupos" not in response.content.decode()


class TestStoreSettingsAdmin:
    def test_changelist_redirects_to_single_record(self, admin_client: Client) -> None:
        response = admin_client.get(reverse("admin:core_storesettings_changelist"))

        assert response.status_code == 302
        assert response["Location"] == reverse(
            "admin:core_storesettings_change", args=[StoreSettings.SINGLETON_PK]
        )

    def test_cannot_add_or_delete(self, admin_client: Client) -> None:
        StoreSettings.load()

        add = admin_client.get(reverse("admin:core_storesettings_add"))
        delete = admin_client.get(
            reverse("admin:core_storesettings_delete", args=[StoreSettings.SINGLETON_PK])
        )

        assert add.status_code == 403
        assert delete.status_code == 403

    def test_change_form_renders(self, admin_client: Client) -> None:
        StoreSettings.load()

        response = admin_client.get(
            reverse("admin:core_storesettings_change", args=[StoreSettings.SINGLETON_PK])
        )

        assert response.status_code == 200
        assert "Pedido pelo WhatsApp" in response.content.decode()
