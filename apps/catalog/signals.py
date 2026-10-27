from typing import Any

from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import ProductImage


@receiver(post_delete, sender=ProductImage)
def delete_image_file(sender: type[ProductImage], instance: ProductImage, **kwargs: Any) -> None:
    """Remove o arquivo do storage quando a foto é apagada (economiza a cota do Cloudinary)."""
    name = instance.image.name
    if name:
        storage = instance.image.storage
        transaction.on_commit(lambda: storage.delete(name))


@receiver(pre_save, sender=ProductImage)
def delete_replaced_image_file(
    sender: type[ProductImage], instance: ProductImage, **kwargs: Any
) -> None:
    """Remove o arquivo antigo quando a foto é trocada por outra."""
    if not instance.pk:
        return
    old_name = ProductImage.objects.filter(pk=instance.pk).values_list("image", flat=True).first()
    if old_name and old_name != instance.image.name:
        storage = instance.image.storage
        transaction.on_commit(lambda: storage.delete(old_name))
