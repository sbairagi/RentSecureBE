# mypy: disable-error-code="import-untyped"
from datetime import timedelta
from typing import Any

from simple_history.models import HistoricalRecords

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from rentsecure_be.type_compat import override


class UpsertMixin:
    """Reusable upsert logic for models with a unique business key."""

    _upsert_filter_fields: tuple[str, ...] = ()
    _upsert_skip_fields: frozenset[str] = frozenset()

    def save(self, *args: Any, **kwargs: Any) -> None:
        existing = self._find_existing_upsert_target()
        if existing is not None:
            self._copy_fields_to_existing(existing)
            existing.save()
            self.pk = existing.pk
            self.__dict__.update(existing.__dict__)
            return
        return super().save(*args, **kwargs)  # type: ignore[misc, no-any-return]

    def _find_existing_upsert_target(self) -> Any | None:
        if self.pk is not None or not self._upsert_filter_fields:
            return None
        filter_kwargs = {
            field: getattr(self, field) for field in self._upsert_filter_fields
        }
        if not all(value is not None for value in filter_kwargs.values()):
            return None
        return (
            type(self)
            .objects.filter(**filter_kwargs)  # type: ignore[attr-defined]
            .first()
        )

    def _copy_fields_to_existing(self, existing: Any) -> None:
        for field in self._meta.fields:  # type: ignore[attr-defined]
            if field.name in self._upsert_skip_fields:
                continue
            setattr(existing, field.attname, getattr(self, field.attname))


# User Models
class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    is_investor = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    whatsapp_number = models.CharField(
        max_length=15, help_text="Include country code, e.g. +91xxxxxxxxxx"
    )
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    @override
    def __str__(self) -> str:
        return self.full_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp_number = models.CharField(
        max_length=15, help_text="Include country code, e.g. +91xxxxxxxxxx"
    )
    whatsapp_opt_in = models.BooleanField(default=True)
    language_preference = models.CharField(
        max_length=2, default="en", choices=[("en", "English"), ("hi", "Hindi")]
    )
    alert_frequency = models.CharField(
        max_length=10,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="weekly",
    )
    receive_rent_alerts = models.BooleanField(default=True)
    receive_tax_alerts = models.BooleanField(default=True)
    receive_vacancy_alerts = models.BooleanField(default=True)
    receive_flagged_alerts = models.BooleanField(default=True)
    receive_voice_alerts = models.BooleanField(default=True)
    greeting_prefix = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom greeting for WhatsApp messages, e.g., 'from Gokul PG'",
    )
    reminder_time = models.TimeField(
        default=timezone.datetime.strptime("09:00", "%H:%M").time(),
        help_text="Preferred time to send WhatsApp rent and tax reminders",
    )
    rent_reminders_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable WhatsApp rent reminders for this owner's renters",
    )
    salary = models.PositiveIntegerField(
        default=0,
        help_text="Annual salary income for ITR calculations",
    )
    other_income = models.PositiveIntegerField(
        default=0,
        help_text="Other annual income for ITR calculations",
    )
    elss_investment = models.PositiveIntegerField(
        default=0,
        help_text="Annual ELSS/PPF/LIC investment claimed under Section 80C",
    )
    has_health_insurance = models.BooleanField(
        default=False,
        help_text="Whether the user has active health insurance for Section 80D",
    )
    home_loan_interest = models.PositiveIntegerField(
        default=0,
        help_text="Annual home loan interest paid for Section 24(b) deduction",
    )
    rent_paid = models.PositiveIntegerField(
        default=0,
        help_text="Annual rent paid for Section 80GG deduction",
    )
    receives_hra = models.BooleanField(
        default=False,
        help_text="Whether the user receives House Rent Allowance (HRA)",
    )
    is_nri = models.BooleanField(
        default=False,
        help_text="Whether the user is a Non-Resident Indian",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City for CA matchmaking",
    )
    total_investment_income = models.PositiveIntegerField(
        default=0,
        help_text="Total investment income for CA specialization matching",
    )


class NotificationPreference(UpsertMixin, models.Model):
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preference"
    )
    push_enabled = models.BooleanField(default=True)
    rent_alerts_push = models.BooleanField(default=True)
    rent_alerts_whatsapp = models.BooleanField(default=True)
    rent_alerts_email = models.BooleanField(default=True)
    monthly_summary_email = models.BooleanField(default=True)
    monthly_summary_whatsapp = models.BooleanField(default=False)
    payout_alerts_whatsapp = models.BooleanField(default=True)
    payout_alerts_email = models.BooleanField(default=False)
    maintenance_push = models.BooleanField(default=True)
    visitor_push = models.BooleanField(default=True)
    agreement_push = models.BooleanField(default=True)
    subscription_push = models.BooleanField(default=True)
    system_push = models.BooleanField(default=True)

    _upsert_filter_fields = ("owner",)
    _upsert_skip_fields = frozenset({"id", "owner"})

    @override
    def __str__(self) -> str:
        return f"Notification Preferences for {self.owner.email or self.owner.username}"


class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    referral_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    MAX_OTP_ATTEMPTS = 5


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self) -> bool:
        return self.used_at is None and (timezone.now() - self.created_at) < timedelta(
            hours=1
        )

    @override
    def __str__(self) -> str:
        return f"Password reset token for {self.user.email or self.user.username}"


# models.py


class OwnerBankDetails(models.Model):
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="bank_details"
    )
    bank_account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    account_holder_name = models.CharField(max_length=100, blank=True, default="")
    beneficiary_id = models.CharField(max_length=100, unique=True, blank=True)
    bank_account_verified = models.BooleanField(default=False)

    @override
    def __str__(self) -> str:
        return f"{self.owner.username} - {self.bank_account_number}"


#  Subscription Models
class SubscriptionPlan(UpsertMixin, models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("elite", "Elite"),
    ]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(help_text="Comma-separated list or rich description")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _upsert_filter_fields = ("name",)
    _upsert_skip_fields = frozenset({"id", "name", "created_at", "updated_at"})

    @override
    def __str__(self) -> str:
        return self.name.capitalize()


class UserSubscription(UpsertMixin, models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="usersubscription"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_yearly = models.BooleanField(default=False)
    tax_reminder_days_before = models.PositiveIntegerField(
        default=7, help_text="Days before tax due date to send reminder"
    )
    rent_reminder_days_before = models.PositiveIntegerField(
        default=7, help_text="Days before rent due date to send reminder"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _upsert_filter_fields = ("user",)
    _upsert_skip_fields = frozenset(
        {"id", "user", "start_date", "created_at", "updated_at"}
    )

    @override
    def __str__(self) -> str:
        return f"{self.user.username} - {self.plan.name if self.plan else 'no plan'}"


class AddOnPurchase(models.Model):
    FEATURE_CHOICES = [
        ("max_buildings", "Max Buildings"),
        ("max_units", "Max Units"),
        ("max_renters", "Max Renters per Unit"),
        ("max_caretakers", "Max Caretakers per Unit"),
        ("max_unit_images", "Max Unit Images"),
        ("max_document_uploads", "Max Document Uploads per Unit"),
        ("tax_notifications", "Tax Notifications"),
        ("whatsapp_alerts", "WhatsApp Alerts"),
        ("rent_agreement_drafting", "Rent Agreement Drafting"),
        ("export_pdf_dossier", "Export PDF Dossier"),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)

    @override
    def __str__(self) -> str:
        return f"{self.name} - {self.user.username}"


class PlanFeatureLimit(UpsertMixin, models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.CASCADE, related_name="limits"
    )
    feature_key = models.CharField(max_length=50, choices=AddOnPurchase.FEATURE_CHOICES)
    value = models.CharField(max_length=20)  # store int or 'unlimited' or 'yes/no'

    class Meta:
        unique_together = ("plan", "feature_key")

    _upsert_filter_fields = ("plan", "feature_key")
    _upsert_skip_fields = frozenset({"id", "plan", "feature_key"})

    @override
    def __str__(self) -> str:
        return f"{self.plan.name} - {self.feature_key}: {self.value}"


class UsageLimit(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_limits"
    )
    feature_key = models.CharField(max_length=50, choices=AddOnPurchase.FEATURE_CHOICES)
    usage_count = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "feature_key")

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if (
            self.pk is None  # type: ignore[unreachable]
            and self.user_id is not None
            and self.feature_key
        ):
            existing = UsageLimit.objects.filter(  # type: ignore[unreachable]
                user_id=self.user_id,
                feature_key=self.feature_key,
            ).first()
            if existing:
                existing.usage_count = self.usage_count
                existing.save()
                self.pk = existing.pk
                self.__dict__.update(existing.__dict__)
                return
        return super().save(*args, **kwargs)  # type: ignore[misc, no-any-return]

    @override
    def __str__(self) -> str:
        return f"{self.user.username} - {self.feature_key}: {self.usage_count}"


# ---------------------------------------------------------------------------
# App Configuration Models
# ---------------------------------------------------------------------------


class AppVersion(models.Model):
    """Single-row table that controls the minimum supported and latest app version."""

    id = models.AutoField(primary_key=True)
    min_supported_version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text="Minimum supported version; users below this must force-update.",
    )
    latest_version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text="Latest released version.",
    )
    is_force_update = models.BooleanField(
        default=False,
        help_text="If True, all users must update regardless of version.",
    )
    store_url = models.URLField(
        blank=True,
        help_text="URL to the app store page for forced updates.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App Version"
        verbose_name_plural = "App Version"

    @override
    def __str__(self) -> str:
        return (
            f"AppVersion(min={self.min_supported_version}, "
            f"latest={self.latest_version})"
        )

    @classmethod
    def get_active(cls) -> "AppVersion":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MaintenanceMode(models.Model):
    """Single-row table that controls the maintenance mode state."""

    id = models.AutoField(primary_key=True)
    is_active = models.BooleanField(
        default=False,
        help_text="Enable or disable maintenance mode.",
    )
    message = models.TextField(
        blank=True,
        default="",
        help_text="Message displayed to users during maintenance.",
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional: when maintenance is scheduled to start.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maintenance Mode"
        verbose_name_plural = "Maintenance Mode"

    @override
    def __str__(self) -> str:
        return f"MaintenanceMode(active={self.is_active})"

    @classmethod
    def get_active(cls) -> "MaintenanceMode":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
