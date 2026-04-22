# from django.test import TestCase
# from django.contrib.auth.models import User
# from properties.models import Building, Unit, Renter, Caretaker, UnitDocument, UnitImage
# from core.models import SubscriptionPlan, UserSubscription, PlanFeatureLimit, AddOnPurchase, UsageLimit
# from datetime import date

# class UnitLimitTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='user1', password='test123')

#         # Subscription plan
#         self.plan = SubscriptionPlan.objects.create(name='pro', monthly_price=100, yearly_price=1000)
#         self.subscription = UserSubscription.objects.create(user=self.user, plan=self.plan, is_active=True)

#         # Plan limits
#         PlanFeatureLimit.objects.bulk_create([
#             PlanFeatureLimit(plan=self.plan, feature_key='max_units', value='2'),
#             PlanFeatureLimit(plan=self.plan, feature_key='max_renters', value='3'),
#             PlanFeatureLimit(plan=self.plan, feature_key='max_caretakers', value='2'),
#             PlanFeatureLimit(plan=self.plan, feature_key='max_document_uploads', value='2'),
#             PlanFeatureLimit(plan=self.plan, feature_key='max_unit_images', value='1'),
#         ])

#         # Building
#         self.building = Building.objects.create(owner=self.user, name="Apt1", address="123 Road")

#     def create_unit(self, number):
#         limit = get_feature_limit(self.user, 'max_units')
#         current_units = Unit.objects.filter(building__owner=self.user).count()
#         if current_units >= limit:
#             raise Exception("Max units limit reached")

#         return Unit.objects.create(building=self.building, unit_number=number)

#     def test_unit_creation_with_limit(self):
#         self.create_unit("101")
#         self.create_unit("102")
#         with self.assertRaises(Exception):
#             self.create_unit("103")

#     def test_renter_creation_within_limit(self):
#         unit = self.create_unit("101")
#         for i in range(3):
#             Renter.objects.create(
#                 unit=unit, name=f"Renter {i}", phone=f"99999999{i}",
#                 id_proof="doc.pdf", rent_agreement="agreement.pdf",
#                 rent_amount=5000, start_date=date.today()
#             )
#         with self.assertRaises(Exception):
#             Renter.objects.create(
#                 unit=unit, name="Renter X", phone="9888888888",
#                 id_proof="doc.pdf", rent_agreement="agreement.pdf",
#                 rent_amount=5000, start_date=date.today()
#             )

#     def test_addon_increases_renter_limit(self):
#         # Upgrade via Add-on
#         AddOnPurchase.objects.create(user=self.user, name='max_renters', amount=100)
#         UsageLimit.objects.create(user=self.user, feature_key='max_renters', usage_count=5)

#         unit = self.create_unit("101")
#         for i in range(5):
#             Renter.objects.create(
#                 unit=unit, name=f"Renter {i}", phone=f"90000000{i}",
#                 id_proof="doc.pdf", rent_agreement="agreement.pdf",
#                 rent_amount=6000, start_date=date.today()
#             )

#         self.assertEqual(unit.renters.count(), 5)

#     def test_caretaker_and_upload_limits(self):
#         unit = self.create_unit("101")

#         # Caretaker (plan allows 2)
#         Caretaker.objects.create(unit=unit, name="CT1", phone="7000000001")
#         Caretaker.objects.create(unit=unit, name="CT2", phone="7000000002")
#         with self.assertRaises(Exception):
#             Caretaker.objects.create(unit=unit, name="CT3", phone="7000000003")

#         # Document uploads (plan allows 2)
#         UnitDocument.objects.create(unit=unit, document="doc1.pdf")
#         UnitDocument.objects.create(unit=unit, document="doc2.pdf")
#         with self.assertRaises(Exception):
#             UnitDocument.objects.create(unit=unit, document="doc3.pdf")

#         # Image uploads (plan allows 1)
#         UnitImage.objects.create(unit=unit, image="img1.png")
#         with self.assertRaises(Exception):
#             UnitImage.objects.create(unit=unit, image="img2.png")
