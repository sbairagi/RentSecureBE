from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import PlanFeatureLimit, SubscriptionPlan


class Command(BaseCommand):
    help = "Seed subscription plans and their feature limits"

    PLAN_DATA = [
        {
            "name": "free",
            "monthly_price": Decimal("0"),
            "yearly_price": Decimal("0"),
            "features": "Basic property management",
            "limits": {
                "max_buildings": "2",
                "max_units": "3",
                "max_renters": "3",
                "max_caretakers": "1",
                "max_unit_images": "3",
                "max_document_uploads": "2",
                "tax_notifications": "yes",
                "whatsapp_alerts": "no",
                "rent_agreement_drafting": "no",
                "export_pdf_dossier": "no",
            },
        },
        {
            "name": "pro",
            "monthly_price": Decimal("29.99"),
            "yearly_price": Decimal("299.99"),
            "features": "Advanced property management with WhatsApp alerts",
            "limits": {
                "max_buildings": "10",
                "max_units": "50",
                "max_renters": "100",
                "max_caretakers": "5",
                "max_unit_images": "20",
                "max_document_uploads": "10",
                "tax_notifications": "yes",
                "whatsapp_alerts": "yes",
                "rent_agreement_drafting": "yes",
                "export_pdf_dossier": "no",
            },
        },
        {
            "name": "elite",
            "monthly_price": Decimal("99.99"),
            "yearly_price": Decimal("999.99"),
            "features": "Unlimited property management with all features",
            "limits": {
                "max_buildings": "unlimited",
                "max_units": "unlimited",
                "max_renters": "unlimited",
                "max_caretakers": "unlimited",
                "max_unit_images": "unlimited",
                "max_document_uploads": "unlimited",
                "tax_notifications": "yes",
                "whatsapp_alerts": "yes",
                "rent_agreement_drafting": "yes",
                "export_pdf_dossier": "yes",
            },
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
            for feature_key, value in plan_info["limits"].items():
                PlanFeatureLimit.objects.update_or_create(
                    plan=plan,
                    feature_key=feature_key,
                    defaults={"value": value},
                )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} plan: {plan.name}")

        self.stdout.write(self.style.SUCCESS("Subscription plans seeded successfully."))
