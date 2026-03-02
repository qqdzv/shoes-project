from django.contrib import admin

from apps.catalog.models import Category, Manufacturer, Product, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["article", "name", "category", "supplier", "price", "discount", "stock_quantity"]
    list_filter = ["category", "supplier", "manufacturer"]
    search_fields = ["article", "name", "description"]
