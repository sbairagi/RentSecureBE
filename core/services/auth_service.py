from __future__ import annotations

from typing import Any

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import Group

from core.models import User
from core.services.base import BaseService, ServiceResult


class AuthService(BaseService):
    """Service for authentication workflows.

    Expected responsibilities:
    - Login and token issuance
    - Token refresh and validation
    - Logout and token revocation
    - Password reset initiation
    """

    @staticmethod
    def login_with_otp(phone: str, group_name: str) -> tuple[User, dict[str, Any]]:
        user, _ = User.objects.get_or_create(phone=phone, defaults={"username": phone})
        user.is_phone_verified = True
        user.save()

        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {"id": user.pk, "phone": user.phone},
        }
        return user, tokens

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
