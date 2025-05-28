# # your_app/management/commands/seed_subscription_plans.py

# from django.core.management.base import BaseCommand
# from core.models import SubscriptionPlan
# from wealth_concierge_platform.models import UsageLimit

# class Command(BaseCommand):
#     help = 'Seed default subscription plans with usage limits'

#     def handle(self, *args, **kwargs):
#         plans_data = [
#             {
#                 'name': 'Free',
#                 'price_monthly': 0,
#                 'price_yearly': 0,
#                 'description': 'Basic access with limited usage',
#                 'limits': {
#                     'max_properties': 1,
#                     'max_uploads': 5,
#                     'max_caretakers': 1,
#                     'max_renters': 3
#                 }
#             },
#             {
#                 'name': 'Pro',
#                 'price_monthly': 499,
#                 'price_yearly': 4999,
#                 'description': 'Advanced tools for property owners',
#                 'limits': {
#                     'max_properties': 10,
#                     'max_uploads': 100,
#                     'max_caretakers': 5,
#                     'max_renters': 5
#                 }
#             },
#             {
#                 'name': 'Elite',
#                 'price_monthly': 1999,
#                 'price_yearly': 19999,
#                 'description': 'Full features for elite users',
#                 'limits': {
#                     'max_properties': 100,
#                     'max_uploads': 1000,
#                     'max_caretakers': 20,
#                     'max_renters': 50
#                 }
#             },
#         ]

#         for plan_data in plans_data:
#             plan, _ = SubscriptionPlan.objects.get_or_create(
#                 name=plan_data['name'],
#                 defaults={
#                     'price_monthly': plan_data['price_monthly'],
#                     'price_yearly': plan_data['price_yearly'],
#                     'description': plan_data['description']
#                 }
#             )
#             UsageLimit.objects.update_or_create(
#                 plan=plan,
#                 defaults=plan_data['limits']
#             )
#         self.stdout.write(self.style.SUCCESS('Subscription plans and usage limits seeded successfully!'))