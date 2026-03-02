from django.urls import path

from apps.catalog.views import (
    ProductCreateView,
    ProductDeleteView,
    ProductEditView,
    ProductListView,
)

app_name = "catalog"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("add/", ProductCreateView.as_view(), name="product_create"),
    path("<str:article>/edit/", ProductEditView.as_view(), name="product_edit"),
    path("<str:article>/delete/", ProductDeleteView.as_view(), name="product_delete"),
]
