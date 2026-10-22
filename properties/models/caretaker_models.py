from typing import Any

from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from rentsecure_be.type_compat import override

# Reuse the shared phone regex if available; otherwise define a local one.
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=(
        "Phone number must be entered in the format: '+999999999'. "
        "Up to 15 digits allowed."
    ),
)


class CareTaker(models.Model):
    """A caretaker / property manager who works for an owner.

    A caretaker belongs to **one owner** — that is the working relationship and
    the plan counts the caretakers of an owner. The work itself is the
    assignment: the caretaker is given buildings and standalone units of that
    owner through :class:`CareTakerAssignment`, and only the assigned
    properties are visible in the caretaker portal.

    ``unit`` is the legacy "home unit" of the caretaker. It is kept so the
    older data keeps working, but it is no longer the scope of the caretaker:
    a caretaker can look after many buildings and many standalone flats. When
    it is left empty the caretaker simply has no home unit registered.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caretakers",
        db_index=True,
    )
    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caretakers",
        db_index=True,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="caretaker_profile",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, help_text="CareTaker full name")
    email = models.EmailField(default="", blank=True)
    phone = models.CharField(
        validators=[phone_regex], max_length=15, help_text="Primary phone"
    )
    alternate_phone = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, help_text="Alternate phone"
    )
    address = models.TextField(blank=True)
    preferred_language = models.CharField(
        max_length=40,
        blank=True,
        help_text="Language the daily summary of the caretaker is written in",
    )
    joining_date = models.DateField(help_text="Date of joining", db_index=True)
    leaving_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(
        default=True, help_text="Currently active?", db_index=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ["-joining_date"]
        verbose_name = "CareTaker"
        verbose_name_plural = "Caretakers"

    @override
    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.leaving_date and self.leaving_date < self.joining_date:
            raise ValidationError("Leaving date cannot be earlier than joining date.")

        if self.owner_id and self.phone:
            same_phone = (
                type(self)
                .objects.filter(owner_id=self.owner_id, phone=self.phone)
                .exclude(pk=self.pk)
            )
            if same_phone.exists():
                raise ValidationError(
                    "This phone number is already on the team of this owner."
                )

        if self.owner_id and self.unit_id:
            unit_owner_id = (
                type(self.unit)
                .objects.filter(pk=self.unit_id)
                .values_list("owner_id", flat=True)
                .first()
            )
            if unit_owner_id is not None and unit_owner_id != self.owner_id:
                raise ValidationError(
                    "The home unit of a caretaker must belong to the same owner."
                )

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Keep the owner in sync with the legacy home unit.

        Older data only knows the unit of a caretaker. When the owner is not
        given, it is derived from that unit so every caretaker keeps exactly
        one owner.
        """
        if self.owner_id is None and self.unit_id is not None:
            owner_id = (
                type(self.unit)
                .objects.filter(pk=self.unit_id)
                .values_list("owner_id", flat=True)
                .first()
            )
            if owner_id is not None:
                self.owner_id = owner_id
                update_fields = kwargs.get("update_fields")
                if update_fields is not None and "owner" not in update_fields:
                    kwargs["update_fields"] = list(update_fields) + ["owner"]
        super().save(*args, **kwargs)

    @override
    def __str__(self) -> str:
        if self.unit_id:
            return f"{self.name} ({self.unit})"
        return f"{self.name} ({self.owner})"


class CareTakerAssignment(models.Model):
    """One property — a building or a standalone unit — in a caretaker's scope.

    A building assignment covers every unit of that building. A unit
    assignment covers a single flat. Exactly one of the two is set.
    """

    class Scope(models.TextChoices):
        BUILDING = "building", "Building"
        UNIT = "unit", "Unit"

    caretaker = models.ForeignKey(
        CareTaker, on_delete=models.CASCADE, related_name="assignments", db_index=True
    )
    building = models.ForeignKey(
        "properties.Building",
        on_delete=models.CASCADE,
        related_name="caretaker_assignments",
        null=True,
        blank=True,
        db_index=True,
    )
    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.CASCADE,
        related_name="caretaker_assignments",
        null=True,
        blank=True,
        db_index=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caretaker_assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["caretaker", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(building__isnull=False, unit__isnull=True)
                    | models.Q(building__isnull=True, unit__isnull=False)
                ),
                name="caretaker_assignment_one_scope",
            ),
            models.UniqueConstraint(
                fields=["caretaker", "building"],
                condition=models.Q(is_active=True, building__isnull=False),
                name="unique_active_caretaker_building",
            ),
            models.UniqueConstraint(
                fields=["caretaker", "unit"],
                condition=models.Q(is_active=True, unit__isnull=False),
                name="unique_active_caretaker_unit",
            ),
        ]

    @override
    def __str__(self) -> str:
        if self.building_id:
            return f"{self.caretaker} → {self.building}"
        return f"{self.caretaker} → {self.unit}"

    @property
    def scope_label(self) -> str:
        """Return the human readable scope of the assignment."""
        if self.building_id:
            return getattr(self.building, "name", "") or "Building"
        return getattr(self.unit, "unit", "") or "Unit"

    @property
    def scope_type(self) -> str:
        """Return ``building`` or ``unit``."""
        return self.Scope.BUILDING if self.building_id else self.Scope.UNIT


class CareTakerAssignmentLog(models.Model):
    caretaker = models.ForeignKey(CareTaker, on_delete=models.CASCADE, db_index=True)
    action = models.CharField(max_length=20, help_text="assigned / unassigned")
    action_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-action_date"]


class CareTakerActivity(models.Model):
    """What a caretaker did on the ground.

    The caretaker works for the owner, so the owner has to be able to see what
    the team did: the job a caretaker took, the status they moved a request to
    and the notes they left. Every action of the caretaker portal writes one
    row here, and the owner reads them in the *What my team did* panel.
    """

    class Action(models.TextChoices):
        TOOK_JOB = "took_job", "Took the job"
        STATUS_CHANGE = "status_change", "Changed the status"
        NOTE = "note", "Added a note"

    caretaker = models.ForeignKey(
        CareTaker, on_delete=models.CASCADE, related_name="activities", db_index=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="caretaker_activities",
        db_index=True,
    )
    maintenance_request = models.ForeignKey(
        "properties.MaintenanceRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caretaker_activities",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    summary = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    from_status = models.CharField(max_length=16, blank=True)
    to_status = models.CharField(max_length=16, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caretaker_activities_made",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["caretaker", "-created_at"]),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.caretaker} · {self.summary}"
