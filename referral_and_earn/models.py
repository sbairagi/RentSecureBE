# models.py
import uuid
from typing import Any, override

from django.conf import settings
from django.db import models


class Referral(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_profile",
    )
    referred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals_made",
    )
    referral_code = models.CharField(max_length=20, unique=True)
    bonus_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4()).split("-", maxsplit=1)[0].upper()
        super().save(*args, **kwargs)
