"""
Smartbot Celery/cron tasks.

This module is intentionally kept minimal. It exists to satisfy the
historical import surface; the signature-polling logic it used to
perform was removed because ``RentRecord`` does not (and never did)
carry ``signature_status`` or ``signature_request_id`` columns. Those
fields live on :class:`properties.models.RentAgreementDraft` (see
``properties.views.unit_views.leegality_webhook`` for the canonical
implementation).
"""

# Keep the symbol below for backward-compatibility with any
# ``from smartbot.tasks import poll_signature_status`` callers.
# The function is a no-op because the underlying feature was retired
# in favour of webhook-driven signature updates on RentAgreementDraft.
def poll_signature_status() -> None:
    """No-op stub retained for backward compatibility.

    Real-time signature updates are now driven by the Leegality webhook
    in :mod:`properties.views.unit_views`.
    """
    return None
