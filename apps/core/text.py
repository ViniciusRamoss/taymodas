from django.db import models
from django.utils.text import slugify


def unique_slugify(instance: models.Model, value: str, field_name: str = "slug") -> str:
    """Gera um slug a partir de `value` que ainda não existe na tabela do `instance`.

    Em caso de colisão, acrescenta um sufixo numérico: `vestido-floral`, `vestido-floral-2`...
    O próprio registro é ignorado, então salvar de novo não muda o slug.
    """
    field = instance._meta.get_field(field_name)
    max_length: int = getattr(field, "max_length", None) or 50
    base = slugify(value)[:max_length].strip("-") or "item"
    queryset = type(instance)._default_manager.exclude(pk=instance.pk)

    slug = base
    suffix = 2
    while queryset.filter(**{field_name: slug}).exists():
        tail = f"-{suffix}"
        slug = f"{base[: max_length - len(tail)].strip('-')}{tail}"
        suffix += 1
    return slug
