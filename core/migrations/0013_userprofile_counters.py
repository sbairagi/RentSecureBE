# Denormalized counter fields on UserProfile for dashboard stats.
# SQLite-only deployment (no Redis, no PostgreSQL) on 2 vRAM Ubuntu server.

import datetime

from django.db import migrations, models


def backfill_counters(apps, schema_editor):
    """Initialize denormalized counters for existing owners."""
    UserProfile = apps.get_model("core", "UserProfile")
    Building = apps.get_model("properties", "Building")
    Unit = apps.get_model("properties", "Unit")
    Renter = apps.get_model("properties", "Renter")
    CareTaker = apps.get_model("properties", "CareTaker")
    RentRecord = apps.get_model("properties", "RentRecord")
    from django.db.models import Q, Sum, F
    from django.db.models import DecimalField
    from django.db.models.functions import Coalesce

    today = datetime.date.today()

    for profile in UserProfile.objects.select_related("user").all():
        user = profile.user
        total_buildings = Building.objects.filter(owner=user, is_archived=False).count()
        total_units = Unit.objects.filter(owner=user, is_archived=False).count()
        occupied_units = Unit.objects.filter(
            owner=user, is_archived=False, status="occupied"
        ).count()
        active_renters = Renter.objects.filter(
            unit__owner=user, status="active"
        ).count()
        caretakers_count = CareTaker.objects.filter(owner=user, is_active=True).count()
        notice_period_renters = Renter.objects.filter(
            unit__owner=user, status="notice_period"
        ).count()
        revoked_renters = Renter.objects.filter(
            unit__owner=user, status="revoked"
        ).count()
        deactivated_renters = Renter.objects.filter(
            unit__owner=user, status="deactivated"
        ).count()

        rents = RentRecord.objects.filter(unit__owner=user)
        pending_rent = (
            rents.exclude(status__in=["paid", "cancelled"]).aggregate(
                total=Coalesce(
                    Sum(F("amount") + F("late_fee") - F("discount"))
                    - Sum("amount_paid"),
                    0,
                    output_field=DecimalField(),
                )
            )["total"]
            or 0
        )
        overdue_rent = (
            rents.filter(
                Q(status="overdue") | Q(status="pending", due_date__lt=today)
            ).aggregate(
                total=Coalesce(
                    Sum(F("amount") + F("late_fee") - F("discount"))
                    - Sum("amount_paid"),
                    0,
                    output_field=DecimalField(),
                )
            )[
                "total"
            ]
            or 0
        )

        profile.total_buildings = total_buildings
        profile.total_units = total_units
        profile.occupied_units = occupied_units
        profile.active_renters = active_renters
        profile.caretakers_count = caretakers_count
        profile.notice_period_renters = notice_period_renters
        profile.revoked_renters = revoked_renters
        profile.deactivated_renters = deactivated_renters
        profile.pending_rent = pending_rent
        profile.overdue_rent = overdue_rent
        from django.utils import timezone

        profile.counters_updated_at = timezone.now()
        profile.save(
            update_fields=[
                "total_buildings",
                "total_units",
                "occupied_units",
                "active_renters",
                "caretakers_count",
                "notice_period_renters",
                "revoked_renters",
                "deactivated_renters",
                "pending_rent",
                "overdue_rent",
                "counters_updated_at",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_emailsigninlink"),
        ("properties", "0021_building_society_contact_caretaker_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="total_buildings",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="total_units",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="occupied_units",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="active_renters",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="caretakers_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="notice_period_renters",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="revoked_renters",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="deactivated_renters",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="pending_rent",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="overdue_rent",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="counters_updated_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.RunPython(backfill_counters, migrations.RunPython.noop),
    ]
