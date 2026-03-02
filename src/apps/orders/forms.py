from django import forms
from django.forms import inlineformset_factory

from apps.accounts.models import CustomUser
from apps.orders.models import Order, OrderItem


class OrderForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=CustomUser.ROLE_CLIENT).order_by("full_name"),
        label="Клиент (ФИО)",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Order
        fields = [
            "order_number",
            "status",
            "pickup_point",
            "order_date",
            "delivery_date",
            "client",
            "pickup_code",
        ]
        widgets = {
            "order_number": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "pickup_point": forms.Select(attrs={"class": "form-select"}),
            "order_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "delivery_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "pickup_code": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "order_number": "Номер заказа",
            "status": "Статус заказа",
            "pickup_point": "Адрес пункта выдачи",
            "order_date": "Дата заказа",
            "delivery_date": "Дата выдачи",
            "pickup_code": "Код получения",
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop("is_edit", False)
        super().__init__(*args, **kwargs)
        if self.is_edit:
            self.fields["order_number"].widget.attrs["readonly"] = True


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }
        labels = {
            "product": "Товар (артикул)",
            "quantity": "Количество",
        }


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
