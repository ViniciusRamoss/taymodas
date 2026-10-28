from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse

from .models import StoreSettings

# Grupos de permissão não são usados (só a dona administra); escondê-los simplifica o menu.
admin.site.unregister(Group)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin[StoreSettings]):
    fieldsets = [
        ("Contato", {"fields": ["whatsapp_number", "instagram_handle", "store_address"]}),
        (
            "Pedido pelo WhatsApp",
            {
                "fields": ["order_message_template"],
                "description": "É assim que a mensagem chega para você quando a cliente clica "
                "em “Pedir no WhatsApp”.",
            },
        ),
        ("Entrega", {"fields": ["mototaxi_cities", "delivery_info"]}),
        ("Sobre", {"fields": ["about_text"]}),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: StoreSettings | None = None) -> bool:
        return False

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, object] | None = None
    ) -> HttpResponseRedirect:
        """Pula a lista (só existe um registro) e abre direto o formulário."""
        obj = StoreSettings.load()
        return HttpResponseRedirect(reverse("admin:core_storesettings_change", args=[obj.pk]))
