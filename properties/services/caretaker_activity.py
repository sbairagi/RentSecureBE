"""What the team of an owner did.

The caretaker works on the ground for one owner. Every action the caretaker
takes in the portal — taking a job, moving a request forward, leaving a note —
writes one row of :class:`~properties.models.CaretakerActivity`, and the
owner reads those rows in the *What my team did* panel.

The writing happens in one place so the trail is the same whatever the action
was, and the reading happens in one place too, so the owner always sees the
whole team.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import QuerySet

if TYPE_CHECKING:
    from properties.models import CareTaker, CareTakerActivity, MaintenanceRequest


def record_activity(
    *,
    caretaker: CareTaker,
    action: str,
    summary: str,
    detail: str = "",
    maintenance_request: MaintenanceRequest | None = None,
    from_status: str = "",
    to_status: str = "",
    actor=None,
) -> CareTakerActivity:
    """Write one row of the trail of the caretaker."""
    from properties.models import CareTakerActivity

    return CareTakerActivity.objects.create(
        caretaker=caretaker,
        owner=caretaker.owner,
        action=action,
        summary=summary[:200],
        detail=detail,
        maintenance_request=maintenance_request,
        from_status=from_status or "",
        to_status=to_status or "",
        actor=actor if getattr(actor, "is_authenticated", False) else None,
    )


def team_activity(
    owner, caretaker_id: int | None = None
) -> QuerySet[CareTakerActivity]:
    """Return the trail of the team of the owner, newest first."""
    from properties.models import CareTakerActivity

    queryset = CareTakerActivity.objects.filter(owner=owner).select_related(
        "caretaker",
        "maintenance_request",
        "maintenance_request__unit",
        "maintenance_request__unit__building",
        "actor",
    )
    if caretaker_id:
        queryset = queryset.filter(caretaker_id=caretaker_id)
    return queryset
