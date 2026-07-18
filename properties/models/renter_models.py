from __future__ import annotations

import builtins
from datetime import date
from typing import Any

from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from core.models import User
from shared.type_compat import override

from .unit_models import Unit

phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=(
        "Phone number must be entered in the format: '+999999999'. "
        "Up to 15 digits allowed."
    ),
)


class Renter(models.Model):
    class RenterStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        NOTICE_PERIOD = "notice_period", "Notice Period"
        REVOKED = "revoked", "Revoked"
        DEACTIVATED = "deactivated", "Deactivated"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not args:
            full_name = kwargs.pop("full_name", None)
            if full_name is not None and "name" not in kwargs:
                kwargs["name"] = full_name
            kwargs.setdefault("id_proof", "id_proof.pdf")
            kwargs.setdefault("rent_agreement", "rent_agreement.pdf")
            kwargs.setdefault("start_date", date.today())
        super().__init__(*args, **kwargs)

    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="renters", db_index=True
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="renter_profile",
    )
    name = models.CharField(max_length=100, help_text="Renter's full name")
    email = models.EmailField(
        default="",
        blank=True,
        help_text="Renter's email for receipts and notifications",
    )
    phone = models.CharField(
        validators=[phone_regex], max_length=15, help_text="Primary phone number"
    )
    alternate_phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        help_text="Alternate phone number",
    )
    emergency_contact_name = models.CharField(
        max_length=100, blank=True, help_text="Emergency contact name"
    )
    emergency_contact_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        help_text="Emergency contact number",
    )
    renter_image = models.ImageField(
        upload_to="renter_image/", blank=True, null=True, help_text="Photo of renter"
    )
    id_proof = models.FileField(
        upload_to="id_proofs/renter/", help_text="Renter's ID proof document"
    )
    rent_agreement = models.FileField(
        upload_to="agreements/", help_text="Rent agreement document"
    )
    rent_amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Rent amount"
    )
    start_date = models.DateField(help_text="Rental start date", db_index=True)
    end_date = models.DateField(null=True, blank=True, help_text="Rental end date")
    is_active = models.BooleanField(
        default=True, help_text="Is renter currently active?"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    whatsapp_number = models.CharField(
        max_length=15, blank=True, help_text="For WhatsApp messages"
    )
    rent_due_date = models.DateField(
        blank=True,
        null=True,
        default=date.today,
        help_text="Required for rent reminder",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Move in Date")
    late_payment_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    missed_rents = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)

    is_agreement_revoked = models.BooleanField(default=False)
    revocation_reason = models.TextField(blank=True)
    revoked_by_owner = models.BooleanField(default=False)
    revoked_on = models.DateTimeField(blank=True, null=True)

    vacated_on = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=RenterStatus.choices, default=RenterStatus.ACTIVE
    )
    notice_start_date = models.DateField(null=True, blank=True)

    final_invoice_path = models.CharField(max_length=255, blank=True)

    # Self-onboarding status
    class OnboardingStatus(models.TextChoices):
        PENDING = "pending", "Pending Invite"
        LINK_SENT = "link_sent", "Link Sent"
        COMPLETED = "completed", "Completed"

    class KYCStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING,
        help_text="Renter self-onboarding progress",
    )
    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.NOT_STARTED,
        help_text="KYC verification status",
    )
    onboarding_token = models.CharField(
        max_length=255,
        blank=True,
        unique=True,
        help_text="Secure token for onboarding link",
    )
    onboarding_link_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When the onboarding link was sent to renter"
    )

    class Meta:
        unique_together = ("unit", "phone")
        ordering = ["-start_date"]

    @override
    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

        # Prevent multiple active/notice_period renters on the same unit
        if self.status in ("active", "notice_period"):
            existing = Renter.objects.filter(
                unit=self.unit,
                status__in=("active", "notice_period"),
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "This unit already has an active or notice-period renter. "
                    "Please deactivate the existing renter before adding a new one."
                )

    @property
    def property(self) -> Unit:
        """Backward-compatible alias for ``self.unit``."""
        return self.unit

    @builtins.property
    def full_name(self) -> str:
        """Backward-compatible alias for ``self.name``."""
        return self.name

    @full_name.setter
    def full_name(self, value: str) -> None:
        self.name = value

    @builtins.property
    def rent_agreement_pdf(self) -> Any | None:
        return self.rent_agreement

    @builtins.property
    def police_verification_pdf(self) -> Any | None:
        if hasattr(self, "policeverification") and self.policeverification is not None:
            return self.policeverification.file
        return None

    @override
    def __str__(self) -> str:
        return self.name


class RentReminderLog(models.Model):
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, help_text="EXAMPLE: PRE, DUE, LATE")
    sent_at = models.DateTimeField(auto_now_add=True)


class AgreementRevocationLog(models.Model):
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE)
    revoked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class ArchivedRenter(models.Model):
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE)
    data = models.JSONField()
    agreement_pdf = models.FileField(upload_to="archived/agreements/")
    police_pdf = models.FileField(upload_to="archived/police/")
    property_images = models.JSONField(default=list)
    final_invoice = models.FileField(upload_to="archived/final_invoice/")
    archived_at = models.DateTimeField(auto_now_add=True)


class RentAgreementDraft(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE, db_index=True)
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="rent_agreement_draft"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="auto_agreements/")
    leegality_document_id = models.CharField(max_length=255, blank=True)
    owner_signed = models.BooleanField(default=False)
    renter_signed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("renter", "unit")

    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    @override
    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.renter.unit != self.unit:
            raise ValidationError("Renter must belong to the specified unit.")


class PoliceVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE, db_index=True)
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="police_verification"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="rent_agreements/")

    class Meta:
        unique_together = ("renter", "unit")

    @override
    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.renter.unit != self.unit:
            raise ValidationError("Renter must belong to the specified unit.")
