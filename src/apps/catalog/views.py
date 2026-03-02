from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.catalog.forms import ProductForm
from apps.catalog.models import Product, Supplier
from apps.catalog.utils import resize_product_image
from apps.orders.models import OrderItem
from config.request import AppRequest

_EDIT_LOCK_KEY = "editing_product_article"


def _get_filtered_products(request: HttpRequest) -> QuerySet[Product]:
    queryset = Product.objects.select_related("category", "supplier", "manufacturer")

    search = request.GET.get("search", "").strip()
    supplier_id = request.GET.get("supplier", "")
    sort = request.GET.get("sort", "")

    if search:
        queryset = queryset.filter(
            Q(article__icontains=search)
            | Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__name__icontains=search)
            | Q(manufacturer__name__icontains=search)
            | Q(supplier__name__icontains=search)
            | Q(unit__icontains=search),
        )

    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    if sort == "stock_asc":
        queryset = queryset.order_by("stock_quantity")
    elif sort == "stock_desc":
        queryset = queryset.order_by("-stock_quantity")

    return queryset


class ProductListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        request.session.pop(_EDIT_LOCK_KEY, None)
        r: AppRequest = request  # type: ignore[assignment]
        user = r.user
        is_guest = not user.is_authenticated
        can_filter = not is_guest and (user.is_admin or user.is_manager)
        can_manage = not is_guest and user.is_admin

        if can_filter:
            products = _get_filtered_products(request)
            suppliers = Supplier.objects.all()
        else:
            products = Product.objects.select_related("category", "supplier", "manufacturer")
            suppliers = []

        context = {
            "products": products,
            "suppliers": suppliers,
            "is_guest": is_guest,
            "can_filter": can_filter,
            "can_manage": can_manage,
            "current_search": request.GET.get("search", ""),
            "current_supplier": request.GET.get("supplier", ""),
            "current_sort": request.GET.get("sort", ""),
        }

        if r.htmx:
            return render(request, "catalog/partials/product_table.html", context)

        return render(request, "catalog/product_list.html", context)


class ProductCreateView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может добавлять товары.")
            return redirect("catalog:product_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "catalog/product_form.html", {"form": ProductForm(), "is_edit": False})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if product.photo:
                resize_product_image(product.photo.path if product.photo.name else None)
            product.save()
            messages.success(request, f"Товар «{product.name}» успешно добавлен.")
            return redirect("catalog:product_list")
        return render(request, "catalog/product_form.html", {"form": form, "is_edit": False})


class ProductEditView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может редактировать товары.")
            return redirect("catalog:product_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, article: str) -> HttpResponse:
        locked = request.session.get(_EDIT_LOCK_KEY)
        if locked and locked != article:
            messages.error(request, "Сначала закройте текущее окно редактирования товара.")
            return redirect("catalog:product_list")
        request.session[_EDIT_LOCK_KEY] = article
        product = get_object_or_404(Product, article=article)
        return render(
            request,
            "catalog/product_form.html",
            {"form": ProductForm(instance=product, is_edit=True), "product": product, "is_edit": True},
        )

    def post(self, request: HttpRequest, article: str) -> HttpResponse:
        product = get_object_or_404(Product, article=article)
        old_photo_path = product.photo.path if product.photo else None
        form = ProductForm(request.POST, request.FILES, instance=product, is_edit=True)
        if form.is_valid():
            new_photo = request.FILES.get("photo")
            if new_photo and old_photo_path and Path(old_photo_path).exists():
                Path(old_photo_path).unlink()
            product = form.save()
            if product.photo:
                resize_product_image(product.photo.path)
            request.session.pop(_EDIT_LOCK_KEY, None)
            messages.success(request, f"Товар «{product.name}» успешно обновлён.")
            return redirect("catalog:product_list")
        return render(
            request,
            "catalog/product_form.html",
            {"form": form, "product": product, "is_edit": True},
        )


class ProductDeleteView(LoginRequiredMixin, View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        r: AppRequest = request  # type: ignore[assignment]
        if not r.user.is_admin:
            messages.error(request, "Доступ запрещён. Только администратор может удалять товары.")
            return redirect("catalog:product_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, article: str) -> HttpResponse:
        product = get_object_or_404(Product, article=article)
        return render(request, "catalog/product_confirm_delete.html", {"product": product})

    def post(self, request: HttpRequest, article: str) -> HttpResponse:
        product = get_object_or_404(Product, article=article)
        if OrderItem.objects.filter(product=product).exists():
            messages.error(
                request,
                f"Нельзя удалить товар «{product.name}»: он присутствует в одном или нескольких заказах.",
            )
            return redirect("catalog:product_list")

        if product.photo and Path(product.photo.path).exists():
            Path(product.photo.path).unlink()

        product_name = product.name
        product.delete()
        messages.success(request, f"Товар «{product_name}» удалён.")
        return redirect("catalog:product_list")
