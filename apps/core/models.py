from __future__ import annotations

from string import Formatter
from typing import Any
from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class TimeStampedModel(models.Model):
    """Base abstrata com datas de criação e atualização."""

    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


ORDER_MESSAGE_FIELDS = ("produto", "tamanho", "cor", "preco", "link")

# Proposta inicial; a dona da loja ajusta no admin.
DEFAULT_ORDER_MESSAGE = (
    "Olá! Quero pedir este produto:\n"
    "{produto}\n"
    "Tamanho: {tamanho}\n"
    "Cor: {cor}\n"
    "Preço: {preco}\n"
    "{link}"
)

DEFAULT_MOTOTAXI_CITIES = "\n".join(
    ["Ribeirão Preto", "Serrana", "Serra Azul", "Cravinhos", "Cajuru", "Jardinópolis"]
)

# Embed público do Google Maps pela busca do endereço: não exige chave nem conta no Google Cloud.
MAP_EMBED_URL = "https://maps.google.com/maps?q={query}&output=embed"
MAP_LINK_URL = "https://www.google.com/maps/search/?api=1&query={query}"
WHATSAPP_URL = "https://wa.me/{number}?text={text}"

WHATSAPP_NUMBER_VALIDATOR = RegexValidator(
    regex=r"^55\d{10,11}$",
    message="Use só números: 55 + DDD + número. Ex.: 5516912345678.",
)


class StoreSettings(models.Model):
    """Configurações gerais da loja. Existe um único registro (singleton)."""

    SINGLETON_PK = 1

    whatsapp_number = models.CharField(
        "número do WhatsApp",
        max_length=13,
        blank=True,
        validators=[WHATSAPP_NUMBER_VALIDATOR],
        help_text=(
            "Só números, começando com 55 e o DDD. Ex.: 5516912345678. "
            "Enquanto estiver vazio, o botão de pedido não aparece no site."
        ),
    )
    order_message_template = models.TextField(
        "mensagem do pedido",
        default=DEFAULT_ORDER_MESSAGE,
        help_text=(
            "Texto que já vem escrito no WhatsApp da cliente. Use as palavras entre chaves "
            "para preencher automaticamente: {produto}, {tamanho}, {cor}, {preco} e {link}."
        ),
    )
    delivery_info = models.TextField(
        "informações de entrega",
        blank=True,
        help_text="Cidades atendidas, envio pelos Correios, prazos, retirada na loja...",
    )
    store_address = models.CharField(
        "endereço da loja",
        max_length=200,
        blank=True,
        default="Rua Onofre Serafim, 148, Serrana-SP",
        help_text=(
            "Rua, número e cidade, como no Google Maps. Aparece no mapa da página de entregas "
            "e no rodapé. Vazio esconde o mapa."
        ),
    )
    mototaxi_cities = models.TextField(
        "cidades com entrega por mototáxi",
        blank=True,
        default=DEFAULT_MOTOTAXI_CITIES,
        help_text="Uma cidade por linha.",
    )
    about_text = models.TextField(
        "sobre a loja",
        blank=True,
        help_text=(
            "Sua história, em poucas linhas. Aparece na página Como comprar; vazio esconde o "
            "trecho."
        ),
    )
    instagram_handle = models.CharField(
        "Instagram",
        max_length=30,
        default="taymodas23",
        help_text="Somente o usuário, sem @.",
    )

    class Meta:
        verbose_name = "configurações da loja"
        verbose_name_plural = "configurações da loja"

    def __str__(self) -> str:
        return "Configurações da loja"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        # O registro é único e necessário; apagar não faz sentido.
        return 0, {}

    def clean(self) -> None:
        names = {
            field for _, field, _, _ in Formatter().parse(self.order_message_template) if field
        }
        unknown = names - set(ORDER_MESSAGE_FIELDS)
        if unknown:
            allowed = ", ".join(f"{{{name}}}" for name in ORDER_MESSAGE_FIELDS)
            raise ValidationError(
                {
                    "order_message_template": (
                        f"Palavra(s) não reconhecida(s): {', '.join(sorted(unknown))}. "
                        f"Use apenas {allowed}."
                    )
                }
            )

    @property
    def mototaxi_city_list(self) -> list[str]:
        return [line.strip() for line in self.mototaxi_cities.splitlines() if line.strip()]

    def whatsapp_url(self, text: str) -> str | None:
        """Conversa com a loja com `text` já escrito; `None` enquanto não há número."""
        if not self.whatsapp_number:
            return None
        return WHATSAPP_URL.format(number=self.whatsapp_number, text=quote(text))

    @property
    def map_embed_url(self) -> str:
        return MAP_EMBED_URL.format(query=quote(self.store_address)) if self.store_address else ""

    @property
    def map_link_url(self) -> str:
        return MAP_LINK_URL.format(query=quote(self.store_address)) if self.store_address else ""

    @classmethod
    def load(cls) -> StoreSettings:
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return obj
