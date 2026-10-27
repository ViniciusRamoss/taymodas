from decimal import Decimal

from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory, ImageField

from apps.catalog.models import Category, Color, Product, ProductImage, ProductVariant, Size


class CategoryFactory(DjangoModelFactory[Category]):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = Sequence(lambda n: f"Categoria {n}")


class SizeFactory(DjangoModelFactory[Size]):
    class Meta:
        model = Size
        django_get_or_create = ("name",)

    name = Sequence(lambda n: f"T{n}")
    position = Sequence(lambda n: n)


class ColorFactory(DjangoModelFactory[Color]):
    class Meta:
        model = Color
        django_get_or_create = ("name",)

    name = Sequence(lambda n: f"Cor {n}")
    hex_code = "#000000"


class ProductFactory(DjangoModelFactory[Product]):
    class Meta:
        model = Product

    name = Sequence(lambda n: f"Produto {n}")
    description = "Descrição de teste."
    price = Decimal("99.90")
    category = SubFactory(CategoryFactory)


class ProductImageFactory(DjangoModelFactory[ProductImage]):
    class Meta:
        model = ProductImage

    product = SubFactory(ProductFactory)
    image = ImageField(width=40, height=60, color="black")


class ProductVariantFactory(DjangoModelFactory[ProductVariant]):
    class Meta:
        model = ProductVariant

    product = SubFactory(ProductFactory)
    size = SubFactory(SizeFactory)
    color = SubFactory(ColorFactory)
    stock = 1
