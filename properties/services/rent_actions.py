"""The action log of a rent record.

Every action a user takes on a rent record leaves a row behind: the month
that was created, the details that were edited, the reason a month was
cancelled, the reminder that was sent and the receipt that was delivered
— or that could not be delivered.

Two trails describe a record:

* the **audit trail** of ``django-simple-history`` says what the *data*
  looks like after a change (a ``+`` when the record was created, a ``~``
  when it was changed);
* the **action log** says what the *user did*.

They are shown together in the history of a record, newest first.  An
action that changed the record carries the id of the audit entry it
explains, so one action is never listed twice.
"""

from __future__ import annotations

import logging
from typing import Any

from properties.models import RentRecord, RentRecordAction

logger = logging.getLogger(__name__)


def latest_history_id(rent_record: RentRecord) -> int | None:
    """The id of the newest audit entry of a record — if there is one.

    Args:
        rent_record: The record the audit entry belongs to.

    Returns:
        The id of the newest entry of the audit trail, or ``None`` when the
        record has never been saved.
    """
    entry = rent_record.history.order_by("-history_id").first()
    return int(entry.history_id) if entry is not None else None


def log_rent_action(
    rent_record: RentRecord,
    kind: str,
    *,
    summary: str = "",
    detail: str = "",
    outcome: str = RentRecordAction.Outcome.RECORDED,
    actor: Any = None,
    history_id: int | None = None,
) -> RentRecordAction | None:
    """Write one action of a user into the trail of a record.

    A trail that cannot be written must never break the action it describes,
    so a failure is logged and swallowed — the action itself still happened.

    Args:
        rent_record: The record the action was taken on.
        kind: What the user did — one of ``RentRecordAction.Kind``.
        summary: One line that says what happened.
        detail: The numbers and the words behind the action.
        outcome: How the action ended — sent, failed or recorded.
        actor: The user who took the action.
        history_id: The audit entry this action explains.

    Returns:
        The action that was written, or ``None`` when it could not be.
    """
    try:
        return RentRecordAction.objects.create(
            rent_record=rent_record,
            kind=kind,
            summary=summary[:200],
            detail=detail,
            outcome=outcome,
            actor=actor if getattr(actor, "pk", None) else None,
            history_id=history_id,
        )
    except Exception:  # pragma: no cover - the trail must not break the action
        logger.exception(
            "The action log for rent %s could not be written", rent_record.pk
        )
        return None
