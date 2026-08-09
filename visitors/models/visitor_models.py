import logging
from datetime import timedelta
from typing import Any

from simple_history.models import HistoricalRecords

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import User
from properties.models import Building, Renter, Unit
from rentsecure_be.type_compat import override

logger = logging.getLogger(__name__)


class VisitorQuerySet(models.QuerySet):
    """Custom queryset for Visitor model."""

    def active(self):
        return self.filter(
            status__in=[
                Visitor.Status.PENDING_APPROVAL,
                Visitor.Status.APPROVED,
                Visitor.Status.CHECKED_IN,
            ]
        )

    def for_owner(self, user: User):
        return self.filter(created_by=user)

    def for_renter(self, user: User):
        return self.filter(renter__user=user)

    def checked_in(self):
        return self.filter(status=Visitor.Status.CHECKED_IN)

    def checked_out(self):
        return self.filter(status=Visitor.Status.CHECKED_OUT)

    def pending_approval(self):
        return self.filter(status=Visitor.Status.PENDING_APPROVAL)

    def expired(self):
        return self.filter(status=Visitor.Status.EXPIRED)

    def recent(self, days: int = 30):
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)


class Visitor(models.Model):
    """Enterprise Visitor model for property access management.

    Supports the full visitor lifecycle:
    REQUESTED → PENDING_APPROVAL → APPROVED → CHECKED_IN → CHECKED_OUT
                ↘ REJECTED / CANCELLED / BLOCKED / EXPIRED
    """

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CHECKED_IN = "checked_in", "Checked In"
        CHECKED_OUT = "checked_out", "Checked Out"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"
        BLOCKED = "blocked", "Blocked"

    class Purpose(models.TextChoices):
        PERSONAL_VISIT = "personal_visit", "Personal Visit"
        FAMILY_VISIT = "family_visit", "Family Visit"
        BUSINESS_MEETING = "business_meeting", "Business Meeting"
        SERVICE_PERSONNEL = "service_personnel", "Service Personnel"
        MAINTENANCE = "maintenance", "Maintenance / Repair"
        DELIVERY = "delivery", "Delivery / Courier"
        EMERGENCY = "emergency", "Emergency"
        OTHER = "other", "Other"

    objects = VisitorQuerySet.as_manager()

    # ─── Identity ────────────────────────────────────────────────────────────
    visitor_name = models.CharField(
        max_length=100,
        help_text="Full name of the visitor",
        db_index=True,
    )
    phone_number = models.CharField(
        max_length=15,
        help_text="Primary contact number of the visitor",
        db_index=True,
    )
    email = models.EmailField(
        blank=True,
        default="",
        help_text="Visitor email address (optional)",
    )
    photo = models.ImageField(
        upload_to="visitor_photos/",
        blank=True,
        null=True,
        help_text="Visitor photo",
    )

    # ─── Visit Details ───────────────────────────────────────────────────────
    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
        default=Purpose.PERSONAL_VISIT,
        help_text="Reason for the visit",
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="visitors",
        help_text="Building being visited",
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="visitors",
        help_text="Unit being visited",
    )
    renter = models.ForeignKey(
        Renter,
        on_delete=models.CASCADE,
        related_name="visitors",
        help_text="Renter being visited",
    )
    visit_date = models.DateField(
        help_text="Date of the scheduled visit",
        db_index=True,
    )
    expected_arrival = models.DateTimeField(
        help_text="Expected arrival date and time",
    )
    expected_departure = models.DateTimeField(
        help_text="Expected departure date and time",
    )
    number_of_visitors = models.PositiveIntegerField(
        default=1,
        help_text="Total number of visitors in the group",
    )
    vehicle_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Vehicle number (if applicable)",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about the visit",
    )

    # ─── Approval ────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_visitors",
        help_text="User who approved this visitor request",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of approval",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for rejection",
    )
    approver_phone = models.CharField(
        max_length=15,
        blank=True,
        default="",
        help_text="Phone of the person who approved",
    )
    approver_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes from the approver",
    )

    # ─── QR Verification ─────────────────────────────────────────────────────
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text="Unique QR token for gate verification",
    )
    qr_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the QR code was generated",
    )
    qr_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="QR code expiry timestamp",
    )
    qr_max_uses = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of times this QR can be scanned",
    )
    qr_used_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the QR has been scanned",
    )
    qr_verified = models.BooleanField(
        default=False,
        help_text="Whether the QR was successfully verified at gate",
    )
    qr_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When QR was verified at gate",
    )

    # ─── Entry / Exit ─────────────────────────────────────────────────────────
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual check-in timestamp",
    )
    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual check-out timestamp",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_visitors",
        help_text="Caretaker/user who verified this visitor at gate",
    )
    verified_by_phone = models.CharField(
        max_length=15,
        blank=True,
        default="",
        help_text="Phone of the verifier",
    )
    vehicle_details = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Vehicle details at time of entry",
    )
    visit_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Visit duration in minutes (calculated on check-out)",
    )

    # ─── OTP Verification ────────────────────────────────────────────────────
    otp_code = models.CharField(
        max_length=6,
        blank=True,
        default="",
        help_text="OTP code for visitor verification",
    )
    otp_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the OTP was generated",
    )
    otp_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="OTP expiry timestamp",
    )
    otp_verified = models.BooleanField(
        default=False,
        help_text="Whether the OTP was successfully verified",
    )
    otp_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the OTP was verified",
    )
    otp_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of OTP verification attempts",
    )
    OTP_MAX_ATTEMPTS = 5
    OTP_EXPIRY_MINUTES = 5

    # ─── Audit ───────────────────────────────────────────────────────────────
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_visitors",
        help_text="User who created this visitor request",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "visit_date"]),
            models.Index(fields=["renter", "status"]),
            models.Index(fields=["building", "status"]),
            models.Index(fields=["qr_token"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["otp_code", "otp_expires_at"]),
        ]
        verbose_name = "Visitor"
        verbose_name_plural = "Visitors"

    @override
    def __str__(self) -> str:
        return f"Visitor: {self.visitor_name} → {self.renter.name} ({self.status})"

    @override
    def clean(self) -> None:
        """Validate visitor data before saving."""
        if self.expected_departure <= self.expected_arrival:
            raise ValidationError("Expected departure must be after expected arrival.")

        if self.renter.unit != self.unit:
            raise ValidationError("Renter must be associated with the specified unit.")

        if self.unit.building != self.building:
            raise ValidationError("Unit must belong to the specified building.")

        if self.unit.owner != self.building.owner:
            raise ValidationError("Unit and building must have the same owner.")

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_otp_expired(self) -> bool:
        if not self.otp_expires_at:
            return True
        return timezone.now() > self.otp_expires_at

    @property
    def is_qr_expired(self) -> bool:
        if not self.qr_expires_at:
            return True
        return timezone.now() > self.qr_expires_at

    @property
    def is_visit_expired(self) -> bool:
        if not self.expected_departure:
            return False
        return timezone.now() > self.expected_departure

    @property
    def can_check_in(self) -> bool:
        return self.status == Visitor.Status.APPROVED and not self.is_visit_expired

    @property
    def can_check_out(self) -> bool:
        return self.status == Visitor.Status.CHECKED_IN

    @property
    def is_completed(self) -> bool:
        return self.status in [
            Visitor.Status.CHECKED_OUT,
            Visitor.Status.EXPIRED,
            Visitor.Status.CANCELLED,
            Visitor.Status.REJECTED,
        ]

    def generate_qr_token(self) -> str:
        """Generate a unique QR token for this visitor."""
        import secrets

        self.qr_token = secrets.token_urlsafe(32)
        self.qr_generated_at = timezone.now()
        self.qr_expires_at = self.expected_departure
        self.qr_max_uses = self.number_of_visitors
        self.qr_used_count = 0
        self.qr_verified = False
        self.save(
            update_fields=[
                "qr_token",
                "qr_generated_at",
                "qr_expires_at",
                "qr_max_uses",
                "qr_used_count",
                "qr_verified",
            ]
        )
        return self.qr_token

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP for visitor verification."""
        import secrets

        self.otp_code = str(secrets.randbelow(900000) + 100000)
        self.otp_generated_at = timezone.now()
        self.otp_expires_at = timezone.now() + timedelta(
            minutes=self.OTP_EXPIRY_MINUTES
        )
        self.otp_attempts = 0
        self.otp_verified = False
        self.save(
            update_fields=[
                "otp_code",
                "otp_generated_at",
                "otp_expires_at",
                "otp_attempts",
                "otp_verified",
            ]
        )
        logger.info("OTP generated for visitor %s", self.id)
        return self.otp_code

    def verify_otp(self, entered_code: str) -> bool:
        """Verify the entered OTP code."""
        self.otp_attempts += 1

        if self.is_otp_expired:
            self.save(update_fields=["otp_attempts"])
            logger.warning("OTP expired for visitor %s", self.id)
            return False

        if self.otp_attempts > self.OTP_MAX_ATTEMPTS:
            self.save(update_fields=["otp_attempts"])
            logger.warning("Max OTP attempts exceeded for visitor %s", self.id)
            return False

        if self.otp_code == entered_code:
            self.otp_verified = True
            self.otp_verified_at = timezone.now()
            self.save(update_fields=["otp_verified", "otp_verified_at", "otp_attempts"])
            logger.info("OTP verified for visitor %s", self.id)
            return True

        self.save(update_fields=["otp_attempts"])
        logger.warning(
            "Invalid OTP attempt for visitor %s (attempt %d)",
            self.id,
            self.otp_attempts,
        )
        return False

    def check_in(self, verified_by_user: User, vehicle_details: str = "") -> None:
        """Check in the visitor."""
        if not self.can_check_in:
            raise ValidationError("Visitor cannot be checked in at this time.")

        self.status = Visitor.Status.CHECKED_IN
        self.check_in_time = timezone.now()
        self.verified_by = verified_by_user
        self.verified_by_phone = verified_by_user.phone
        self.vehicle_details = vehicle_details
        self.qr_verified = True
        self.qr_verified_at = timezone.now()
        self.qr_used_count += 1
        self.save(
            update_fields=[
                "status",
                "check_in_time",
                "verified_by",
                "verified_by_phone",
                "vehicle_details",
                "qr_verified",
                "qr_verified_at",
                "qr_used_count",
            ]
        )
        logger.info("Visitor %s checked in by %s", self.id, verified_by_user.id)

    def check_out(self) -> None:
        """Check out the visitor."""
        if not self.can_check_out:
            raise ValidationError("Visitor cannot be checked out at this time.")

        self.status = Visitor.Status.CHECKED_OUT
        self.check_out_time = timezone.now()

        if self.check_in_time:
            delta = self.check_out_time - self.check_in_time
            self.visit_duration_minutes = int(delta.total_seconds() / 60)

        self.save(
            update_fields=[
                "status",
                "check_out_time",
                "visit_duration_minutes",
            ]
        )
        logger.info("Visitor %s checked out", self.id)

    def approve(self, approved_by_user: User, notes: str = "") -> None:
        """Approve the visitor request."""
        if self.status not in [
            Visitor.Status.PENDING_APPROVAL,
            Visitor.Status.REQUESTED,
        ]:
            raise ValidationError(
                "Visitor request cannot be approved in current status."
            )

        self.status = Visitor.Status.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.approver_notes = notes
        self.approver_phone = approved_by_user.phone
        self.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "approver_notes",
                "approver_phone",
            ]
        )
        logger.info("Visitor %s approved by %s", self.id, approved_by_user.id)

    def reject(self, rejected_by_user: User, reason: str = "") -> None:
        """Reject the visitor request."""
        if self.status not in [
            Visitor.Status.PENDING_APPROVAL,
            Visitor.Status.REQUESTED,
        ]:
            raise ValidationError(
                "Visitor request cannot be rejected in current status."
            )

        self.status = Visitor.Status.REJECTED
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.approver_phone = rejected_by_user.phone
        self.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "rejection_reason",
                "approver_phone",
            ]
        )
        logger.info("Visitor %s rejected by %s", self.id, rejected_by_user.id)

    def cancel(self) -> None:
        """Cancel the visitor request."""
        if self.status in [Visitor.Status.CHECKED_IN, Visitor.Status.CHECKED_OUT]:
            raise ValidationError(
                "Cannot cancel a visitor who has already checked in or out."
            )

        self.status = Visitor.Status.CANCELLED
        self.save(update_fields=["status"])
        logger.info("Visitor %s cancelled", self.id)

    def block(self) -> None:
        """Block the visitor."""
        self.status = Visitor.Status.BLOCKED
        self.save(update_fields=["status"])
        logger.info("Visitor %s blocked", self.id)

    def mark_expired(self) -> None:
        """Mark the visitor as expired."""
        self.status = Visitor.Status.EXPIRED
        self.save(update_fields=["status"])
        logger.info("Visitor %s marked as expired", self.id)


class VisitorHistory(models.Model):
    """Audit trail for visitor status changes."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CHECKED_IN = "checked_in", "Checked In"
        CHECKED_OUT = "checked_out", "Checked Out"
        CANCELLED = "cancelled", "Cancelled"
        BLOCKED = "blocked", "Blocked"
        EXPIRED = "expired", "Expired"
        QR_GENERATED = "qr_generated", "QR Generated"
        QR_VERIFIED = "qr_verified", "QR Verified"
        OTP_GENERATED = "otp_generated", "OTP Generated"
        OTP_VERIFIED = "otp_verified", "OTP Verified"

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name="history",
        db_index=True,
    )
    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )
    description = models.TextField(blank=True, default="")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visitor_history_actions",
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional context (e.g., vehicle number, approver notes)",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["visitor", "action", "created_at"]),
        ]
        verbose_name = "Visitor History"
        verbose_name_plural = "Visitor Histories"

    @override
    def __str__(self) -> str:
        return (
            f"{self.visitor.visitor_name} - {self.get_action_display()}"
            f" ({self.created_at})"
        )
