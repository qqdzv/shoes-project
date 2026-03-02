from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    article = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="Артикул",
    )
    name = models.CharField(max_length=200, verbose_name="Наименование")
    unit = models.CharField(max_length=20, verbose_name="Единица измерения")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Цена",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name="Поставщик",
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        verbose_name="Производитель",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория",
    )
    discount = models.PositiveIntegerField(
        default=0,
        verbose_name="Скидка (%)",
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество на складе",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    photo = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True,
        verbose_name="Фото",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["name"]

    def __str__(self):
        return f"{self.article} — {self.name}"

    @property
    def final_price(self):
        if self.discount > 0:
            return round(self.price * (1 - Decimal(self.discount) / 100), 2)
        return self.price

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def row_css_class(self):
        if not self.is_in_stock:
            return "table-info"
        if self.discount > 15:
            return "row-big-discount"
        return ""
