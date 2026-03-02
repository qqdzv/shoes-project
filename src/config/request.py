from typing import Any

from django.http import HttpRequest

from apps.accounts.models import CustomUser


class AppRequest(HttpRequest):
    user: CustomUser
    htmx: Any
