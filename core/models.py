from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords
from django.conf import settings

# User Models
class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    is_investor = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    whatsapp_number = models.CharField(max_length=15, help_text="Include country code, e.g. +91xxxxxxxxxx")
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.full_name
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp_number = models.CharField(max_length=15, help_text="Include country code, e.g. +91xxxxxxxxxx")
    whatsapp_opt_in = models.BooleanField(default=True)
    language_preference = models.CharField(max_length=2, default="en", choices=[("en", "English"), ("hi", "Hindi")])


class NotificationPreference(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    rent_alerts_whatsapp = models.BooleanField(default=True)
    rent_alerts_email = models.BooleanField(default=True)
    monthly_summary_email = models.BooleanField(default=True)
    monthly_summary_whatsapp = models.BooleanField(default=False)
    payout_alerts_whatsapp = models.BooleanField(default=True)
    payout_alerts_email = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification Preferences for {self.owner.email or self.owner.username}"


class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    referral_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)


# models.py

class OwnerBankDetails(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)  # or PropertyOwner if you have that
    bank_account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    beneficiary_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    bank_account_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner.username} - {self.bank_account_number}"

   
#  Subscription Models
class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
    ]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(help_text="Comma-separated list or rich description")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name.capitalize()
    
class UserSubscription(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usersubscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_yearly = models.BooleanField(default=False)
    tax_reminder_days_before = models.PositiveIntegerField(default=7, help_text="Days before tax due date to send reminder")
    rent_reminder_days_before = models.PositiveIntegerField(default=7, help_text="Days before rent due date to send reminder")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class AddOnPurchase(models.Model):
    FEATURE_CHOICES = [
        ('max_buildings', 'Max Buildings'),
        ('max_units', 'Max Units'),
        ('max_renters', 'Max Renters per Unit'),
        ('max_caretakers', 'Max Caretakers per Unit'),
        ('max_unit_images', 'Max Unit Images'),
        ('max_document_uploads', 'Max Document Uploads per Unit'),
        ('tax_notifications', 'Tax Notifications'),
        ('whatsapp_alerts', 'WhatsApp Alerts'),
        ('rent_agreement_drafting', 'Rent Agreement Drafting'),
        ('export_pdf_dossier', 'Export PDF Dossier'),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
class PlanFeatureLimit(models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='limits')
    feature_key = models.CharField(max_length=50, choices=AddOnPurchase.FEATURE_CHOICES)
    value = models.CharField(max_length=20)  # store int or 'unlimited' or 'yes/no'

    class Meta:
        unique_together = ('plan', 'feature_key')

    def __str__(self):
        return f"{self.plan.name} - {self.feature_key}: {self.value}"
    
class UsageLimit(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_limits')
    feature_key = models.CharField(max_length=50, choices=AddOnPurchase.FEATURE_CHOICES)
    usage_count = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'feature_key')

    def __str__(self):
        return f"{self.user.username} - {self.feature_key}: {self.usage_count}"
    