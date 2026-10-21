"""Canonical subscription plan limits.

This module is the single source of truth for the feature limits that the
backend enforces. It is imported by:

* :mod:`core.signals` — the plan assigned to a newly registered user,
* :mod:`management.commands.seed_subscription_plans` — the operator seeding
  or re-seeding the plan catalogue,
* :mod:`core.migrations` — the data migration that backfills existing
  deployments.

Two families of keys exist.

``max_*`` keys and boolean flags (``yes``/``no``)
    Catalogue metadata. They are rendered by the web subscription screen and
    document what a plan includes.

Quota keys (:data:`QUOTA_FEATURE_KEYS`)
    Hard counters tracked per user in ``UsageLimit``. ``FeatureEnforcer``
    resolves a quota key against the plan's ``PlanFeatureLimit`` row and
    treats a **missing** row as ``0`` (see
    ``properties.feature_enforcer.FeatureEnforcer._get_plan_limit``).

That last rule is the important one: a plan that does not define a quota key
silently blocks the matching workflow. A plan without a
``rent_agreement_drafts`` row resolved to a limit of ``0``, so agreement
uploads were rejected for every subscriber on that plan with
*"You have reached your draft creation limit."* Every plan therefore has to
define every quota key.
"""

from __future__ import annotations

from typing import Final

UNLIMITED: Final[str] = "unlimited"

#: Keys that :class:`~properties.feature_enforcer.FeatureEnforcer` counts per
#: user. A plan must define all of them or the matching workflow is blocked.
QUOTA_FEATURE_KEYS: Final[tuple[str, ...]] = (
    "unit_images",
    "unit_documents",
    "rent_records",
    "rent_agreement_drafts",
)

#: The plan handed to a newly registered user.
FREE_PLAN_LIMITS: Final[dict[str, str]] = {
    "max_buildings": "2",
    "max_units": "3",
    "max_renters": "3",
    "max_caretakers": "1",
    "max_unit_images": "3",
    "max_document_uploads": "2",
    "unit_images": "3",
    "unit_documents": "2",
    "rent_records": "12",
    # Raised from "1": one draft for the whole portfolio blocked every
    # additional agreement upload.
    "rent_agreement_drafts": "10",
    "tax_notifications": "yes",
    "whatsapp_alerts": "no",
    "rent_agreement_drafting": "yes",
    "export_pdf_dossier": "no",
}

#: Paid tier. Quota keys mirror the catalogue caps so both stay consistent.
PRO_PLAN_LIMITS: Final[dict[str, str]] = {
    "max_buildings": "10",
    "max_units": "50",
    "max_renters": "100",
    "max_caretakers": "5",
    "max_unit_images": "20",
    "max_document_uploads": "10",
    "unit_images": "20",
    "unit_documents": "10",
    "rent_records": UNLIMITED,
    "rent_agreement_drafts": UNLIMITED,
    "tax_notifications": "yes",
    "whatsapp_alerts": "yes",
    "rent_agreement_drafting": "yes",
    "export_pdf_dossier": "no",
}

#: Top tier: everything is unlimited.
ELITE_PLAN_LIMITS: Final[dict[str, str]] = {
    "max_buildings": UNLIMITED,
    "max_units": UNLIMITED,
    "max_renters": UNLIMITED,
    "max_caretakers": UNLIMITED,
    "max_unit_images": UNLIMITED,
    "max_document_uploads": UNLIMITED,
    "unit_images": UNLIMITED,
    "unit_documents": UNLIMITED,
    "rent_records": UNLIMITED,
    "rent_agreement_drafts": UNLIMITED,
    "tax_notifications": "yes",
    "whatsapp_alerts": "yes",
    "rent_agreement_drafting": "yes",
    "export_pdf_dossier": "yes",
}

#: Plan name -> limit map. The only place plan limits are defined.
PLAN_LIMITS: Final[dict[str, dict[str, str]]] = {
    "free": FREE_PLAN_LIMITS,
    "pro": PRO_PLAN_LIMITS,
    "elite": ELITE_PLAN_LIMITS,
}


def limits_for_plan(plan_name: str) -> dict[str, str]:
    """Return the canonical limits for ``plan_name`` (empty when unknown)."""
    return PLAN_LIMITS.get(plan_name.lower(), {})


def is_raising_limit(current: str, target: str) -> bool:
    """Return ``True`` when moving from ``current`` to ``target`` raises a limit.

    Used by the data migration so that applying the canonical catalogue can
    only ever loosen a limit, never tighten one that an operator has already
    configured.
    """
    if target == UNLIMITED:
        return current != UNLIMITED
    if current == UNLIMITED:
        return False
    try:
        return int(target) > int(current)
    except (TypeError, ValueError):
        return False
