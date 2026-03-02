import shutil
from datetime import date, datetime
from pathlib import Path

import openpyxl
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import CustomUser
from apps.catalog.models import Category, Manufacturer, Product, Supplier
from apps.orders.models import Order, OrderItem, PickupPoint

IMPORT_DIR = Path(settings.BASE_DIR).parent / "data"

STATUS_MAP = {
    "Завершен": Order.STATUS_COMPLETED,
    "Завершён": Order.STATUS_COMPLETED,
    "Новый": Order.STATUS_NEW,
    "Новый ": Order.STATUS_NEW,
    "В обработке": Order.STATUS_PROCESSING,
    "Отменен": Order.STATUS_CANCELLED,
}


class Command(BaseCommand):
    help = "Импортирует данные из xlsx-файлов папки import/ в базу данных"

    def handle(self, *_args, **_options) -> None:
        print("=" * 50)
        print("Начало импорта данных")
        print("=" * 50)

        self._create_superuser()
        self._import_users()
        self._import_products()
        self._import_pickup_points()
        self._import_orders()

        print("\nИмпорт завершён успешно!")

    def _create_superuser(self) -> None:
        print("\n[0/4] Создание суперпользователя...")
        email = "admin@admin.com"
        if CustomUser.objects.filter(email=email).exists():
            print("  Суперпользователь уже существует, пропускаем.")
            return
        CustomUser.objects.create_superuser(email=email, password="admin", full_name="Admin")  # nosec B106  # pragma: allowlist secret
        print(f"  Создан суперпользователь: {email} / admin")

    def _open_xlsx(self, filename: str) -> list:
        path = IMPORT_DIR / filename
        if not path.exists():
            msg = f"Файл не найден: {path}"
            raise CommandError(msg)
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        return [row for row in rows[1:] if any(cell is not None for cell in row)]

    def _import_users(self) -> None:
        print("\n[1/4] Импорт пользователей...")

        role_map = {
            "Администратор": CustomUser.ROLE_ADMIN,
            "Менеджер": CustomUser.ROLE_MANAGER,
            "Авторизированный клиент": CustomUser.ROLE_CLIENT,
        }

        rows = self._open_xlsx("user_import.xlsx")
        created = 0
        skipped = 0

        for row in rows:
            role_name, full_name, email, password = row[0], row[1], row[2], row[3]
            if not email:
                continue

            role = role_map.get(role_name, CustomUser.ROLE_CLIENT)
            full_name = full_name or ""
            password_str = str(password)

            if CustomUser.objects.filter(email=email).exists():
                skipped += 1
            else:
                user = CustomUser(email=email, username=email, full_name=full_name, role=role)
                user.set_password(password_str)
                user.save()
                created += 1

            if role != CustomUser.ROLE_CLIENT:
                local, domain = email.split("@", 1)
                client_email = f"{local}_client@{domain}"
                if not CustomUser.objects.filter(email=client_email).exists():
                    client_user = CustomUser(
                        email=client_email,
                        username=client_email,
                        full_name=full_name,
                        role=CustomUser.ROLE_CLIENT,
                    )
                    client_user.set_password(password_str)
                    client_user.save()
                    created += 1

        print(f"  Создано: {created}, пропущено (уже есть): {skipped}")

    def _import_products(self) -> None:
        print("\n[2/4] Импорт товаров...")

        rows = self._open_xlsx("Tovar.xlsx")
        media_products = settings.MEDIA_ROOT / "products"
        media_products.mkdir(parents=True, exist_ok=True)

        created = 0
        skipped = 0

        for row in rows:
            article = row[0]
            if not article:
                continue

            article = str(article).strip()

            if Product.objects.filter(article=article).exists():
                skipped += 1
                continue

            name = str(row[1]) if row[1] else ""
            unit = str(row[2]) if row[2] else "шт."
            price = row[3] or 0
            supplier_name = str(row[4]) if row[4] else "Не указан"
            manufacturer_name = str(row[5]) if row[5] else "Не указан"
            category_name = str(row[6]) if row[6] else "Без категории"
            discount = int(row[7]) if row[7] else 0
            stock_quantity = int(row[8]) if row[8] else 0
            description = str(row[9]).strip() if row[9] else ""
            photo_filename = str(row[10]).strip() if row[10] else None

            category, _ = Category.objects.get_or_create(name=category_name)
            supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
            manufacturer, _ = Manufacturer.objects.get_or_create(name=manufacturer_name)

            product = Product(
                article=article,
                name=name,
                unit=unit,
                price=price,
                supplier=supplier,
                manufacturer=manufacturer,
                category=category,
                discount=discount,
                stock_quantity=stock_quantity,
                description=description,
            )

            if photo_filename:
                src = IMPORT_DIR / photo_filename
                if src.exists():
                    dst = media_products / photo_filename
                    if not dst.exists():
                        shutil.copy2(src, dst)
                    product.photo = f"products/{photo_filename}"

            product.save()
            created += 1

        print(f"  Создано: {created}, пропущено (уже есть): {skipped}")

    def _import_pickup_points(self) -> None:
        print("\n[3/4] Импорт пунктов выдачи...")

        rows = self._open_xlsx("Пункты выдачи_import.xlsx")
        created = 0
        skipped = 0

        for row in rows:
            address = row[0]
            if not address:
                continue
            address = str(address).strip()
            _, was_created = PickupPoint.objects.get_or_create(address=address)
            if was_created:
                created += 1
            else:
                skipped += 1

        print(f"  Создано: {created}, пропущено (уже есть): {skipped}")

    def _parse_order_items(self, items_str: str) -> list[tuple[str, int]]:
        if not items_str:
            return []
        parts = [p.strip() for p in str(items_str).split(",")]
        result = []
        i = 0
        while i < len(parts) - 1:
            article = parts[i]
            try:
                qty = int(parts[i + 1])
                result.append((article, qty))
                i += 2
            except (ValueError, IndexError):
                i += 1
        return result

    def _parse_order_date(self, raw) -> date:
        if isinstance(raw, date):
            return raw.date() if hasattr(raw, "time") else raw
        try:
            return datetime.strptime(str(raw), "%d.%m.%Y").date()  # noqa: DTZ007
        except ValueError:
            return date(2025, 1, 1)

    def _parse_delivery_date(self, raw) -> date | None:
        if isinstance(raw, date):
            return raw.date() if hasattr(raw, "time") else raw
        return None

    def _resolve_pickup_point(self, idx_raw, pickup_points: list) -> PickupPoint | None:
        try:
            idx = int(idx_raw) - 1
            return pickup_points[idx] if 0 <= idx < len(pickup_points) else pickup_points[0]
        except (ValueError, TypeError, IndexError):
            return pickup_points[0] if pickup_points else None

    def _create_order_items(self, order: Order, items_str: str) -> None:
        for article, qty in self._parse_order_items(items_str):
            try:
                product = Product.objects.get(article=article)
                OrderItem.objects.create(order=order, product=product, quantity=qty)
            except Product.DoesNotExist:
                print(f"  Товар '{article}' не найден, позиция пропущена")

    def _import_orders(self) -> None:
        print("\n[4/4] Импорт заказов...")

        rows = self._open_xlsx("Заказ_import.xlsx")
        pickup_points = list(PickupPoint.objects.all().order_by("id"))

        created = 0
        skipped = 0

        for row in rows:
            order_number = row[0]
            if not order_number:
                continue

            try:
                order_number = int(order_number)
            except (ValueError, TypeError):
                continue

            if Order.objects.filter(order_number=order_number).exists():
                skipped += 1
                continue

            pickup_point = self._resolve_pickup_point(row[4], pickup_points)
            if not pickup_point:
                print(f"  Нет пунктов выдачи, пропускаем заказ {order_number}")
                continue

            client_full_name = str(row[5]).strip() if row[5] else ""
            try:
                client = CustomUser.objects.get(full_name=client_full_name, role=CustomUser.ROLE_CLIENT)
            except CustomUser.DoesNotExist:
                print(f"  Клиент '{client_full_name}' не найден (роль: client), заказ {order_number} пропущен")
                skipped += 1
                continue

            order = Order.objects.create(
                order_number=order_number,
                order_date=self._parse_order_date(row[2]),
                delivery_date=self._parse_delivery_date(row[3]),
                pickup_point=pickup_point,
                client=client,
                pickup_code=int(row[6]) if row[6] else 0,
                status=STATUS_MAP.get(str(row[7]).strip() if row[7] else "Новый", Order.STATUS_NEW),
            )

            self._create_order_items(order, row[1])
            created += 1

        print(f"  Создано: {created}, пропущено (уже есть): {skipped}")
