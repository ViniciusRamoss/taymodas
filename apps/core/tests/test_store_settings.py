import pytest
from django.core.exceptions import ValidationError

from apps.core.models import DEFAULT_ORDER_MESSAGE, StoreSettings

pytestmark = pytest.mark.django_db


def test_load_creates_single_record_with_defaults() -> None:
    first = StoreSettings.load()
    second = StoreSettings.load()

    assert first.pk == second.pk == StoreSettings.SINGLETON_PK
    assert StoreSettings.objects.count() == 1
    assert first.order_message_template == DEFAULT_ORDER_MESSAGE
    assert first.whatsapp_number == ""
    assert str(first) == "Configurações da loja"


def test_saving_new_instance_overwrites_singleton() -> None:
    StoreSettings.load()
    StoreSettings(whatsapp_number="5516912345678").save()

    assert StoreSettings.objects.count() == 1
    assert StoreSettings.load().whatsapp_number == "5516912345678"


def test_delete_is_a_no_op() -> None:
    settings = StoreSettings.load()

    settings.delete()

    assert StoreSettings.objects.exists()


def test_default_message_is_valid() -> None:
    StoreSettings.load().full_clean()


def test_rejects_unknown_placeholder_in_message() -> None:
    settings = StoreSettings(order_message_template="Pedido: {itens}, {total}, cor {cores}")

    with pytest.raises(ValidationError, match="cores"):
        settings.full_clean()


@pytest.mark.parametrize("number", ["5516912345678", "551632345678"])
def test_accepts_brazilian_whatsapp_number(number: str) -> None:
    StoreSettings(whatsapp_number=number).full_clean()


@pytest.mark.parametrize("number", ["16912345678", "+5516912345678", "55 16 91234-5678"])
def test_rejects_badly_formatted_number(number: str) -> None:
    with pytest.raises(ValidationError, match=r"55 \+ DDD"):
        StoreSettings(whatsapp_number=number).full_clean()
