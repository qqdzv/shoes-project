from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class PickupPoint(models.Model):
    address = models.CharField(
        max_length=300,
        unique=True,
        verbose_name="Адрес",
    )

    class Meta:
        verbose_name = "Пункт выдачи"
        verbose_name_plural = "Пункты выдачи"
        ordering = ["address"]

    def __str__(self):
        return self.address


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_COMPLETED, "Завершен"),
        (STATUS_CANCELLED, "Отменен"),
    ]

    order_number = models.PositiveIntegerField(
        primary_key=True,
        verbose_name="Номер заказа",
    )
    order_date = models.DateField(verbose_name="Дата заказа")
    delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата выдачи",
    )
    pickup_point = models.ForeignKey(
        PickupPoint,
        on_delete=models.PROTECT,
        verbose_name="Пункт выдачи",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={"role": "client"},
        verbose_name="Клиент",
    )
    pickup_code = models.PositiveIntegerField(verbose_name="Код получения")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-order_number"]

    def __str__(self):
        return f"Заказ №{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.article} × {self.quantity}"
