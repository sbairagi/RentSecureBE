from django.db import models
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords
from core.models import User
from django.conf import settings


# Phone number validator for consistent format
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Property(models.Model):
    id = models.AutoField(primary_key=True)

    class PropertyType(models.TextChoices):
        LAND = 'land', 'Land'
        FLAT = 'flat', 'Flat'
        COMMERCIAL_SHOP = 'commercial_shop', 'Commercial Shop'
        HOUSE = 'house', 'House'
        VILLA = 'villa', 'Villa'
        OFFICE = 'office', 'Office'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=100, help_text="Title of the property")
    address_line = models.CharField(max_length=255, help_text="Street address")
    landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Nearby landmark")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=100, help_text="State")
    country = models.CharField(max_length=100, help_text="Country")
    postal_code = models.CharField(max_length=20, help_text="Postal code")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="For WhatsApp messages")
    property_type = models.CharField(max_length=50, choices=PropertyType.choices, help_text="Type of property")
    property_image = models.ImageField(upload_to='property_images/', blank=True, null=True, help_text="Image of property")
    id_proof = models.FileField(upload_to='id_proofs/owners/', help_text="Owner ID proof document")
    is_vacant = models.BooleanField(default=True, help_text="Is property currently vacant?")
    is_verified = models.BooleanField(default=False, help_text="Has property been verified?")
    maintenance_notes = models.TextField(blank=True, null=True, help_text="Maintenance related notes")
    rent_due_reminder = models.BooleanField(default=True, help_text="Enable rent due reminders?")
    agreement_expiry_reminder = models.BooleanField(default=True, help_text="Enable agreement expiry reminders?")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude coordinate")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['owner']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city}, {self.state}"
    
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class PropertyDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='property_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Caretaker(models.Model):
    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='caretakers')
    name = models.CharField(max_length=100, help_text="Caretaker's full name")
    phone = models.CharField(validators=[phone_regex], max_length=15, help_text="Primary phone number")
    alternate_phone = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Alternate phone number")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="For WhatsApp messages")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, help_text="Emergency contact name")
    emergency_contact_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Emergency contact number")
    caretaker_image = models.ImageField(upload_to='caretaker_image/', blank=True, null=True, help_text="Photo of caretaker")
    id_proof = models.FileField(upload_to='id_proof/caretaker/', help_text="Caretaker's ID proof document")
    address_line = models.CharField(max_length=255, help_text="Caretaker address line")
    landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Nearby landmark")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=100, help_text="State")
    country = models.CharField(max_length=100, help_text="Country")
    postal_code = models.CharField(max_length=20, help_text="Postal code")
    start_date = models.DateField(blank=True, null=True, help_text="Start date of caretaker service")
    end_date = models.DateField(blank=True, null=True, help_text="End date of caretaker service")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def clean(self):
        # Optional: Custom validation to ensure end_date > start_date
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")


class Renter(models.Model):
    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='renters')
    name = models.CharField(max_length=100, help_text="Renter's full name")
    phone = models.CharField(validators=[phone_regex], max_length=15, help_text="Primary phone number")
    alternate_phone = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Alternate phone number")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, help_text="Emergency contact name")
    emergency_contact_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Emergency contact number")
    renter_image = models.ImageField(upload_to='renter_image/', blank=True, null=True, help_text="Photo of renter")
    id_proof = models.FileField(upload_to='id_proofs/renter/', help_text="Renter's ID proof document")
    rent_agreement = models.FileField(upload_to='agreements/', help_text="Rent agreement document")
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rent amount")
    start_date = models.DateField(help_text="Rental start date")
    end_date = models.DateField(null=True, blank=True, help_text="Rental end date")
    is_active = models.BooleanField(default=True, help_text="Is renter currently active?")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="For WhatsApp messages")
    rent_due_date = models.DateField(blank=True, null=True, help_text="Required for rent reminder") 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

class RentAgreementDraft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='auto_agreements/')


class PDFExportRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    exported_at = models.DateTimeField(auto_now_add=True)


class RentRecord(models.Model):
    id = models.AutoField(primary_key=True)
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE, related_name='rent_records')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rent_records')
    rent_month = models.DateField(help_text="Use first day of the month, e.g. 2025-05-01")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for rent")
    date_paid = models.DateField(help_text="Date when payment was made")
    
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CHEQUE = 'cheque', 'Cheque'
        ONLINE = 'online', 'Online Transfer'
        OTHER = 'other', 'Other'

    payment_mode = models.CharField(max_length=20, choices=PaymentMode.choices, blank=True, null=True, help_text="Mode of payment")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ('renter', 'rent_month')
        ordering = ['-rent_month']

    def __str__(self):
        return f"{self.renter.name} - {self.rent_month.strftime('%B %Y')}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative.")
        if self.date_paid < self.rent_month:
            raise ValidationError("Date paid cannot be before the rent month.")


class PropertyTaxRecord(models.Model):
    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tax_records')
    tax_year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    payment_mode = models.CharField(max_length=30, choices=[('online', 'Online'), ('cheque', 'Cheque'), ('cash', 'Cash'), ('upi', 'UPI'), ('other', 'Other')], null=True, blank=True)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proof = models.FileField(upload_to='tax_proofs/', null=True, blank=True)
    proof_description = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    internal_notes = models.TextField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_tax_records')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'tax_year')

    def is_due_soon(self, days_before=7):
        from datetime import date, timedelta
        if self.is_paid or not self.due_date:
            return False
        return self.due_date <= date.today() + timedelta(days=days_before)

    def __str__(self):
        return f"{self.property.title} - {self.tax_year}"
    
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
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g. "Extra Storage", "Legal Drafting"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
class PlanFeatureLimit(models.Model):
    FEATURE_CHOICES = [
        ('max_properties', 'Max Properties'),
        ('max_renters', 'Max Renters per Property'),
        ('max_caretakers', 'Max Caretakers per Property'),
        ('max_property_images', 'Max Property Images'),
        ('max_document_uploads', 'Max Document Uploads'),
        ('tax_notifications', 'Tax Notifications'),
        ('whatsapp_alerts', 'WhatsApp Alerts'),
        ('rent_agreement_drafting', 'Rent Agreement Drafting'),
        ('export_pdf_dossier', 'Export PDF Dossier'),
    ]

    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='limits')
    feature_key = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    value = models.CharField(max_length=20)  # store int or 'unlimited' or 'yes/no'

    class Meta:
        unique_together = ('plan', 'feature_key')

    def __str__(self):
        return f"{self.plan.name} - {self.feature_key}: {self.value}"
    
class UsageLimit(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_limits')
    feature_key = models.CharField(max_length=50, choices=PlanFeatureLimit.FEATURE_CHOICES)
    usage_count = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'feature_key')

    def __str__(self):
        return f"{self.user.username} - {self.feature_key}: {self.usage_count}"
    