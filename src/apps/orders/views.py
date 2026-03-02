from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.orders.forms import OrderForm, OrderItemFormSet
from apps.orders.models import Order
from config.request import AppRequest


def _get_filtered_orders(request: HttpRequest) -> QuerySet[Order]:
    queryset = Order.objects.select_related("pickup_point", "client").prefetch_related("items__product")

    search = request.GET.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(order_number__icontains=search)
            | Q(client__full_name__icontains=search)
            | Q(status__icontains=search)
            | Q(pickup_point__address__icontains=search)
            | Q(items__product__article__icontains=search)
            | Q(items__product__name__icontains=search),
        ).distinct()

    return queryset


class OrderListView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        r: AppRequest = request  # type: ignore[assignment]
        if not (r.user.is_admin or r.user.is_manager):
            messages.error(request, "Доступ запрещён. Раздел доступен только менеджерам и администраторам.")
            return redirect("catalog:product_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        r: AppRequest = request  # type: ignore[assignment]
        orders = _get_filtered_orders(request)
        context = {
            "orders": orders,
            "can_manage": r.user.is_admin,
            "current_search": request.GET.get("search", ""),
        }
        if r.htmx:
            return render(request, "orders/partials/order_table.html", context)
        return render(request, "orders/order_list.html", context)


class OrderCreateView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может создавать заказы.")
            return redirect("orders:order_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "orders/order_form.html",
            {"form": OrderForm(), "formset": OrderItemFormSet(), "is_edit": False},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.instance = order
            formset.save()
            messages.success(request, f"Заказ №{order.order_number} успешно создан.")
            return redirect("orders:order_list")
        return render(
            request,
            "orders/order_form.html",
            {"form": form, "formset": formset, "is_edit": False},
        )


class OrderEditView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может редактировать заказы.")
            return redirect("orders:order_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, order_number: int) -> HttpResponse:
        order = get_object_or_404(Order, order_number=order_number)
        return render(
            request,
            "orders/order_form.html",
            {"form": OrderForm(instance=order, is_edit=True), "formset": OrderItemFormSet(instance=order), "order": order, "is_edit": True},
        )

    def post(self, request: HttpRequest, order_number: int) -> HttpResponse:
        order = get_object_or_404(Order, order_number=order_number)
        form = OrderForm(request.POST, instance=order, is_edit=True)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Заказ №{order.order_number} успешно обновлён.")
            return redirect("orders:order_list")
        return render(
            request,
            "orders/order_form.html",
            {"form": form, "formset": formset, "order": order, "is_edit": True},
        )


class OrderDeleteView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может удалять заказы.")
            return redirect("orders:order_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, order_number: int) -> HttpResponse:
        order = get_object_or_404(Order, order_number=order_number)
        return render(request, "orders/order_confirm_delete.html", {"order": order})

    def post(self, request: HttpRequest, order_number: int) -> HttpResponse:
        order = get_object_or_404(Order, order_number=order_number)
        order.delete()
        messages.success(request, f"Заказ №{order_number} удалён.")
        return redirect("orders:order_list")
