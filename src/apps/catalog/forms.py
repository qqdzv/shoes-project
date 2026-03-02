from django import forms

from apps.catalog.models import Product, Supplier


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "article",
            "name",
            "category",
            "description",
            "manufacturer",
            "supplier",
            "price",
            "unit",
            "stock_quantity",
            "discount",
            "photo",
        ]
        widgets = {
            "article": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "manufacturer": forms.Select(attrs={"class": "form-select"}),
            "supplier": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "article": "Артикул",
            "name": "Наименование товара",
            "category": "Категория",
            "description": "Описание",
            "manufacturer": "Производитель",
            "supplier": "Поставщик",
            "price": "Цена (руб.)",
            "unit": "Единица измерения",
            "stock_quantity": "Количество на складе",
            "discount": "Скидка (%)",
            "photo": "Фото товара",
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop("is_edit", False)
        super().__init__(*args, **kwargs)
        if self.is_edit:
            self.fields["article"].widget.attrs["readonly"] = True

        self.fields["supplier"] = forms.ModelChoiceField(
            queryset=Supplier.objects.all(),
            widget=forms.Select(attrs={"class": "form-select"}),
            label="Поставщик",
        )

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            msg = "Цена не может быть отрицательной."
            raise forms.ValidationError(msg)
        return price

    def clean_stock_quantity(self):
        qty = self.cleaned_data.get("stock_quantity")
        if qty is not None and qty < 0:
            msg = "Количество на складе не может быть отрицательным."
            raise forms.ValidationError(msg)
        return qty

    def clean_discount(self):
        discount = self.cleaned_data.get("discount")
        if discount is not None and (discount < 0 or discount > 100):
            msg = "Скидка должна быть от 0 до 100%."
            raise forms.ValidationError(msg)
        return discount
