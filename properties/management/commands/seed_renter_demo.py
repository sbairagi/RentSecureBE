"""Seed the portal with a renter and everything around them.

The command fills the development database with one owner, one caretaker, one
renter with a tenancy, the months of the rent ledger, the agreement waiting
for a signature, a verified police verification, the requests of the flat and
a few vacant homes to explore.

    python manage.py seed_renter_demo
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import User
from properties.models import (
    Building,
    CareTaker,
    CareTakerAssignment,
    MaintenanceRequest,
    PoliceVerification,
    RentAgreementDraft,
    Renter,
    RentRecord,
    RentRecordPart,
    Unit,
    ViewingAppointment,
)
from properties.services.agreement_document_service import generate_agreement_document

OWNER_EMAIL = "owner@securenest.in"
RENTER_EMAIL = "renter@securenest.in"
CARETAKER_EMAIL = "caretaker@securenest.in"
DEMO_CREDENTIAL = "securenest123"


class Command(BaseCommand):
    help = "Seed the database with the renter demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove the demo data before seeding it again.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        owner = self._owner()
        caretaker = self._caretaker(owner)
        building = self._building(owner)
        unit = self._unit(owner, building, "A-101", Unit.VacancyStatus.OCCUPIED)
        other_units = [
            self._unit(owner, building, "A-102", Unit.VacancyStatus.VACANT),
            self._unit(owner, building, "A-201", Unit.VacancyStatus.VACANT),
        ]
        self._unit(owner, building, "A-203", Unit.VacancyStatus.OCCUPIED)
        villa = self._villa(owner)

        renter, renter_user = self._renter(owner, unit)
        self._caretaker_building_assignment(caretaker, building)
        self._caretaker_assignment(caretaker, villa)
        self._ledger(renter, unit)
        self._agreement(owner, renter, unit)
        self._verification(owner, renter, unit)
        self._maintenance(owner, renter, unit)
        self._appointments(renter, renter_user, other_units[0], building)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready — the owner signs in with "
                f"{OWNER_EMAIL} / {DEMO_CREDENTIAL}, the renter with "
                f"{RENTER_EMAIL} / {DEMO_CREDENTIAL} and the caretaker with "
                f"{CARETAKER_EMAIL} / {DEMO_CREDENTIAL}."
            )
        )

    # ------------------------------------------------------------------
    def _reset(self) -> None:
        """Remove the demo data, in the order the links allow."""
        from properties.models import ExtraCharge

        renter = Renter.objects.filter(email=RENTER_EMAIL).first()
        if renter is not None:
            RentRecord.objects.filter(renter=renter).delete()
            ExtraCharge.objects.filter(renter=renter).delete()
            PoliceVerification.objects.filter(renter=renter).delete()
            RentAgreementDraft.objects.filter(renter=renter).delete()
            MaintenanceRequest.objects.filter(renter=renter).delete()
            ViewingAppointment.objects.filter(renter=renter).delete()
            Renter.objects.filter(pk=renter.pk).delete()

        owner = User.objects.filter(email=OWNER_EMAIL).first()
        if owner is not None:
            CareTakerAssignment.objects.filter(caretaker__owner=owner).delete()
            CareTaker.objects.filter(owner=owner).delete()
            Unit.objects.filter(owner=owner).delete()
            Building.objects.filter(owner=owner).delete()
            User.objects.filter(pk=owner.pk).delete()

        caretaker_user = User.objects.filter(email=CARETAKER_EMAIL).first()
        if caretaker_user is not None:
            caretaker_user.delete()

        self.stdout.write("Old demo data removed.")

    def _owner(self) -> User:
        owner, created = User.objects.get_or_create(
            email=OWNER_EMAIL,
            defaults={
                "username": OWNER_EMAIL,
                "full_name": "Arjun Mehta",
                "phone": "+919845011223",
            },
        )
        if created:
            owner.set_password(DEMO_CREDENTIAL)
            owner.save()
        group, _ = Group.objects.get_or_create(name="owner")
        owner.groups.add(group)
        return owner

    def _caretaker(self, owner: User) -> CareTaker:
        """The caretaker of the owner, with the account they sign in with."""
        user, created = User.objects.get_or_create(
            email=CARETAKER_EMAIL,
            defaults={
                "username": CARETAKER_EMAIL,
                "full_name": "Kavita Rao",
                "phone": "+919876543210",
            },
        )
        if created:
            user.set_password(DEMO_CREDENTIAL)
            user.save()
        group, _ = Group.objects.get_or_create(name="caretaker")
        user.groups.add(group)

        caretaker, _ = CareTaker.objects.get_or_create(
            owner=owner,
            name="Kavita Rao",
            defaults={
                "user": user,
                "phone": "+919876543210",
                "email": CARETAKER_EMAIL,
                "joining_date": date.today() - timedelta(days=120),
            },
        )
        if caretaker.user_id != user.id:
            caretaker.user = user
            caretaker.save(update_fields=["user"])
        return caretaker

    def _building(self, owner: User) -> Building:
        building, _ = Building.objects.get_or_create(
            owner=owner,
            name="Lakeview Residency",
            defaults={
                "address_line": "24th Main Road, HSR Layout",
                "city": "Bengaluru",
                "state": "Karnataka",
                "country": "India",
                "postal_code": "560102",
            },
        )
        return building

    def _unit(self, owner: User, building: Building, label: str, status: str) -> Unit:
        unit, _ = Unit.objects.get_or_create(
            owner=owner,
            building=building,
            unit=label,
            defaults={
                "unit_type": "flat",
                "address_line": "24th Main Road, HSR Layout",
                "city": "Bengaluru",
                "state": "Karnataka",
                "country": "India",
                "postal_code": "560102",
                "rent_amount": Decimal("28000"),
                "status": status,
            },
        )
        if unit.status != status:
            unit.status = status
            unit.save(update_fields=["status"])
        return unit

    def _villa(self, owner: User) -> Unit:
        unit, _ = Unit.objects.get_or_create(
            owner=owner,
            building=None,
            unit="Villa 5",
            defaults={
                "unit_type": "villa",
                "address_line": "5 Baner Road",
                "city": "Pune",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "411045",
                "rent_amount": Decimal("42000"),
                "status": Unit.VacancyStatus.VACANT,
            },
        )
        return unit

    def _renter(self, owner: User, unit: Unit) -> tuple[Renter, User]:
        user, created = User.objects.get_or_create(
            email=RENTER_EMAIL,
            defaults={
                "username": RENTER_EMAIL,
                "full_name": "Riya Kapoor",
                "phone": "+919845099887",
            },
        )
        if created:
            user.set_password(DEMO_CREDENTIAL)
            user.save()
        group, _ = Group.objects.get_or_create(name="renter")
        user.groups.add(group)

        renter, _ = Renter.objects.get_or_create(
            user=user,
            defaults={
                "unit": unit,
                "name": "Riya Kapoor",
                "email": RENTER_EMAIL,
                "phone": "+919845099887",
                "alternate_phone": "+919845099888",
                "emergency_contact_name": "Sameer Kapoor",
                "emergency_contact_number": "+919845099888",
                "rent_amount": Decimal("28000"),
                "start_date": date(2026, 4, 1),
                "end_date": date(2027, 3, 31),
                "status": "active",
            },
        )
        return renter, user

    def _caretaker_assignment(self, caretaker: CareTaker, unit: Unit) -> None:
        CareTakerAssignment.objects.get_or_create(
            caretaker=caretaker, unit=unit, defaults={"is_active": True}
        )

    def _caretaker_building_assignment(
        self, caretaker: CareTaker, building: Building
    ) -> None:
        """A building assignment covers every home of that building."""
        CareTakerAssignment.objects.get_or_create(
            caretaker=caretaker,
            building=building,
            defaults={"is_active": True},
        )

    def _ledger(self, renter: Renter, unit: Unit) -> None:
        today = date.today()
        first = date(today.year, today.month, 1)
        for months_back in range(6, 0, -1):
            month = first
            for _ in range(months_back):
                month = (month - timedelta(days=1)).replace(day=1)
            due = month.replace(day=5)
            if due > today:
                continue
            record, created = RentRecord.objects.get_or_create(
                unit=unit,
                due_date=due,
                defaults={
                    "renter": renter,
                    "amount": Decimal("28000"),
                    "amount_paid": Decimal("28000"),
                    "payment_method": RentRecord.PaymentMethod.UPI,
                    "status": RentRecord.Status.PAID,
                    "paid_on": due - timedelta(days=1),
                    "transaction_id": f"UPI-{month.strftime('%Y%m')}",
                },
            )
            if created:
                RentRecordPart.objects.create(
                    rent_record=record,
                    amount=Decimal("28000"),
                    paid_on=record.paid_on,
                    payment_method=RentRecord.PaymentMethod.UPI,
                    transaction_id=record.transaction_id,
                    receipt_no=f"RC-{month.strftime('%Y-%m')}-00087",
                )

        # the month that is open right now
        current = date(today.year, today.month, 5)
        if current <= today:
            current = date(today.year, today.month, 1) + timedelta(days=4)
        RentRecord.objects.get_or_create(
            unit=unit,
            due_date=current,
            defaults={
                "renter": renter,
                "amount": Decimal("28000"),
                "amount_paid": Decimal("0"),
                "payment_method": RentRecord.PaymentMethod.UPI,
                "status": RentRecord.Status.PENDING,
                "payment_link": "https://pay.securenest.in/rent",
            },
        )

    def _agreement(self, owner: User, renter: Renter, unit: Unit) -> RentAgreementDraft:
        agreement, created = RentAgreementDraft.objects.get_or_create(
            renter=renter,
            defaults={
                "user": owner,
                "unit": unit,
                "monthly_rent": Decimal("28000"),
                "security_deposit": Decimal("56000"),
                "start_date": renter.start_date,
                "end_date": renter.end_date,
                "rent_due_day": 5,
                "payment_mode": "bank_transfer",
                "notice_period_months": 2,
                "jurisdiction": "Bengaluru, Karnataka",
                "witness_name": "Kavita Rao",
                "special_clauses": (
                    "No pets inside the flat. Parking is one per flat and is not "
                    "covered by the rent."
                ),
                "owner_signed": True,
                "owner_signed_at": timezone.now(),
            },
        )
        if created or not agreement.document_generated_at:
            generate_agreement_document(agreement)
        agreement.status = agreement.refresh_status()
        agreement.save(update_fields=["status"])
        return agreement

    def _verification(
        self, owner: User, renter: Renter, unit: Unit
    ) -> PoliceVerification:
        verification, created = PoliceVerification.objects.get_or_create(
            renter=renter,
            defaults={
                "user": owner,
                "unit": unit,
                "status": PoliceVerification.PoliceVerificationStatus.VERIFIED,
                "submitted_at": timezone.now() - timedelta(days=12),
                "verified_at": timezone.now() - timedelta(days=10),
                "reviewed_at": timezone.now() - timedelta(days=10),
                "reviewed_by": owner,
            },
        )
        if created and not verification.file:
            verification.file.save(
                "police-verification-riya.pdf",
                ContentFile(b"%PDF-1.4 demo verification document"),
                save=True,
            )
        return verification

    def _maintenance(self, owner: User, renter: Renter, unit: Unit) -> None:
        MaintenanceRequest.objects.get_or_create(
            owner=owner,
            unit=unit,
            renter=renter,
            title="Bedroom fan stopped working",
            defaults={
                "description": (
                    "The fan in the second bedroom stopped two days ago. It is "
                    "warm in the room at night."
                ),
                "category": MaintenanceRequest.Category.ELECTRICAL,
                "priority": MaintenanceRequest.Priority.HIGH,
                "status": MaintenanceRequest.Status.IN_PROGRESS,
                "reported_at": timezone.now() - timedelta(days=2),
            },
        )
        MaintenanceRequest.objects.get_or_create(
            owner=owner,
            unit=unit,
            renter=renter,
            title="Kitchen tap dripping",
            defaults={
                "description": "The tap was replaced. Closing this request.",
                "category": MaintenanceRequest.Category.PLUMBING,
                "priority": MaintenanceRequest.Priority.MEDIUM,
                "status": MaintenanceRequest.Status.RESOLVED,
                "reported_at": timezone.now() - timedelta(days=30),
                "resolved_at": timezone.now() - timedelta(days=25),
            },
        )

    def _appointments(
        self,
        renter: Renter,
        renter_user: User,
        unit: Unit,
        building: Building,
    ) -> None:
        ViewingAppointment.objects.get_or_create(
            renter_user=renter_user,
            unit=unit,
            defaults={
                "renter": renter,
                "scheduled_for": timezone.now() + timedelta(days=3),
                "mode": ViewingAppointment.Mode.IN_PERSON,
                "status": ViewingAppointment.Status.REQUESTED,
                "notes": "I would like to see the flat in the evening.",
            },
        )
