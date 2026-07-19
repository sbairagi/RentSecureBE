import warnings
from typing import Any

from django.conf import settings
from django.db import models

from shared.fields import EncryptedCharField
from shared.type_compat import override


class OwnerBankDetails(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_bank_details",
    )
    bank_account_number = EncryptedCharField(max_length=30)
    ifsc_code = EncryptedCharField(max_length=20)
    account_holder_name = models.CharField(max_length=100, blank=True, default="")
    beneficiary_id = models.CharField(max_length=100, unique=True, blank=True)
    bank_account_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "payment_ownerbankdetails"
        verbose_name = "Owner Bank Details"
        verbose_name_plural = "Owner Bank Details"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "owner" in kwargs:
            warnings.warn(
                "payments.models.OwnerBankDetails is the canonical model. "
                "core.models.OwnerBankDetails is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
        super().__init__(*args, **kwargs)

    @override
    def __str__(self) -> str:
        return f"{self.owner.username} - {self.bank_account_number}"
