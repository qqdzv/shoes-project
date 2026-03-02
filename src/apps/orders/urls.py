from django.urls import path

from apps.orders.views import OrderCreateView, OrderDeleteView, OrderEditView, OrderListView

app_name = "orders"

urlpatterns = [
    path("", OrderListView.as_view(), name="order_list"),
    path("add/", OrderCreateView.as_view(), name="order_create"),
    path("<int:order_number>/edit/", OrderEditView.as_view(), name="order_edit"),
    path("<int:order_number>/delete/", OrderDeleteView.as_view(), name="order_delete"),
]
