from django.contrib import admin

from apps.orders.models import Order, OrderItem, PickupPoint


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ["address"]
    search_fields = ["address"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "client", "status", "order_date", "delivery_date"]
    list_filter = ["status"]
    search_fields = ["order_number", "client__full_name"]
    inlines = [OrderItemInline]
