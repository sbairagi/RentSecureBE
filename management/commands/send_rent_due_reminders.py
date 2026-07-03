#     def handle(self, *args, **kwargs):
#         renters = Renter.objects.filter(rent_due_date__isnull=False)


#             days_before = subscription.plan.rent_reminder_days_before or 7
#             due_date = renter.rent_due_date
#             reminder_date = due_date - timedelta(days=days_before)


#                 self.stdout.write(self.style.SUCCESS(
#                     f"Sent rent due reminder to {user.username} for renter {renter.name} (due on {due_date})"
#                 ))
