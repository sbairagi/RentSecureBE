from __future__ import annotations

from typing import Any

from core.services.base import BaseService, ServiceResult


class PasswordService(BaseService):
    """Service for password management workflows.

    Expected responsibilities:
    - Password change validation
    - Password reset orchestration
    - Password policy enforcement
    """

    @staticmethod
    def change_password(user: Any, old_password: str, new_password: str) -> None:
        if not old_password or not new_password:
            raise ValueError("Both old and new passwords are required.")
        if not user.check_password(old_password):
            raise ValueError("Old password is incorrect.")
        if old_password == new_password:
            raise ValueError("New password must be different.")
        user.set_password(new_password)
        user.save()

    @staticmethod
    def reset_password(user: Any, new_password: str) -> None:
        if not new_password:
            raise ValueError("New password is required.")
        user.set_password(new_password)
        user.save()

    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
