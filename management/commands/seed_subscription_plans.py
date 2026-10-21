from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import PlanFeatureLimit, SubscriptionPlan
from core.plan_limits import PLAN_LIMITS


class Command(BaseCommand):
    help = "Seed subscription plans and their feature limits"

    PLAN_DATA = [
        {
            "name": "free",
            "monthly_price": Decimal("0"),
            "yearly_price": Decimal("0"),
            "features": "Basic property management",
        },
        {
            "name": "pro",
            "monthly_price": Decimal("29.99"),
            "yearly_price": Decimal("299.99"),
            "features": "Advanced property management with WhatsApp alerts",
        },
        {
            "name": "elite",
            "monthly_price": Decimal("99.99"),
            "yearly_price": Decimal("999.99"),
            "features": "Unlimited property management with all features",
        },
    ]

    def handle(self, *args, **options):
        for plan_info in self.PLAN_DATA:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_info["name"],
                defaults={
                    "monthly_price": plan_info["monthly_price"],
                    "yearly_price": plan_info["yearly_price"],
                    "features": plan_info["features"],
                    "is_active": True,
                },
            )
            for feature_key, value in PLAN_LIMITS[plan_info["name"]].items():
                PlanFeatureLimit.objects.update_or_create(
                    plan=plan,
                    feature_key=feature_key,
                    defaults={"value": value},
                )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} plan: {plan.name}")

        self.stdout.write(self.style.SUCCESS("Subscription plans seeded successfully."))
