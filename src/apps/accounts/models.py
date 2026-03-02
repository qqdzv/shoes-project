from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            msg = "Email обязателен"
            raise ValueError(msg)
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.ROLE_ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_CLIENT = "client"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Администратор"),
        (ROLE_MANAGER, "Менеджер"),
        (ROLE_CLIENT, "Авторизированный клиент"),
    ]

    email = models.EmailField(unique=True, verbose_name="Логин (email)")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CLIENT,
        verbose_name="Роль",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.full_name

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    @property
    def is_client(self):
        return self.role == self.ROLE_CLIENT
