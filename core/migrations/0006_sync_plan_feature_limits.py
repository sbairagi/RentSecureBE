"""Backfill plan feature limits and raise the agreement draft quota.

Plans that predate the canonical limit catalogue can be missing quota rows
(``unit_images``, ``unit_documents``, ``rent_records``,
``rent_agreement_drafts``). ``FeatureEnforcer`` resolves a missing row to
``0``, so those plans blocked the matching workflow outright — most visibly
the rent agreement upload, which failed with *"You have reached your draft
creation limit."* for every subscriber.

The migration creates missing rows and only ever *raises* an existing value;
an operator-configured limit is never tightened.
"""

from django.db import migrations

from core.plan_limits import PLAN_LIMITS, is_raising_limit


def apply_canonical_limits(apps, schema_editor):
    PlanFeatureLimit = apps.get_model("core", "PlanFeatureLimit")
    SubscriptionPlan = apps.get_model("core", "SubscriptionPlan")

    for plan_name, limits in PLAN_LIMITS.items():
        plan = SubscriptionPlan.objects.filter(name=plan_name).first()
        if plan is None:
            continue
        for feature_key, target in limits.items():
            limit = PlanFeatureLimit.objects.filter(
                plan=plan, feature_key=feature_key
            ).first()
            if limit is None:
                PlanFeatureLimit.objects.create(
                    plan=plan, feature_key=feature_key, value=target
                )
            elif is_raising_limit(limit.value, target):
                limit.value = target
                limit.save(update_fields=["value"])


def revert_canonical_limits(apps, schema_editor):
    """No-op: raising a limit cannot be automatically undone safely."""


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_add_push_preferences"),
    ]

    operations = [
        migrations.RunPython(
            apply_canonical_limits,
            revert_canonical_limits,
        ),
    ]
