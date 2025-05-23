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


class Caretaker(models.Model):
    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='caretakers')
    name = models.CharField(max_length=100, help_text="Caretaker's full name")
    phone = models.CharField(validators=[phone_regex], max_length=15, help_text="Primary phone number")
    alternate_phone = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Alternate phone number")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, help_text="Emergency contact name")
    emergency_contact_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Emergency contact number")
    caretaker_image = models.ImageField(upload_to='caretaker_images/', blank=True, null=True, help_text="Photo of caretaker")
    id_proof = models.FileField(upload_to='id_proofs/caretakers/', help_text="Caretaker's ID proof document")
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
    renter_image = models.ImageField(upload_to='renter_images/', blank=True, null=True, help_text="Photo of renter")
    id_proof = models.FileField(upload_to='id_proofs/renters/', help_text="Renter's ID proof document")
    rent_agreement = models.FileField(upload_to='agreements/', help_text="Rent agreement document")
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rent amount")
    start_date = models.DateField(help_text="Rental start date")
    end_date = models.DateField(null=True, blank=True, help_text="Rental end date")
    is_active = models.BooleanField(default=True, help_text="Is renter currently active?")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
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

