from django.db import models
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords
from core.models import User
from django.conf import settings
from datetime import date


# Phone number validator for consistent format
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

class Building(models.Model):
    name = models.CharField(max_length=255)
    address_line = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buildings')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'address_line', 'city', 'owner')

class Unit(models.Model):
    id = models.AutoField(primary_key=True)

    class UnitType(models.TextChoices):
        LAND = 'land', 'Land'
        FLAT = 'flat', 'Flat'
        COMMERCIAL_SHOP = 'commercial_shop', 'Commercial Shop'
        HOUSE = 'house', 'House'
        VILLA = 'villa', 'Villa'
        OFFICE = 'office', 'Office'
        PAYING_GUEST = 'paying_guest', 'Paying Guest'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unit', db_index=True)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='units')
    is_archived = models.BooleanField(default=False)
    building_name = models.CharField(max_length=100, blank=True, null=True, help_text="name of the building")
    unit = models.CharField(max_length=100, help_text="unit of the unit")
    address_line = models.CharField(max_length=255, help_text="Street address")
    landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Nearby landmark")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=100, help_text="State")
    country = models.CharField(max_length=100, help_text="Country")
    postal_code = models.CharField(max_length=20, help_text="Postal code")
    # whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="For WhatsApp messages")
    unit_type = models.CharField(max_length=50, choices=UnitType.choices, help_text="Type of unit")
    # unit_image = models.ImageField(upload_to='unit_images/', blank=True, null=True, help_text="Image of unit")
    # id_proof = models.FileField(upload_to='id_proofs/owners/', help_text="Owner ID proof document")
    status = models.CharField(max_length=20, choices=[("vacant", "Vacant"),("occupied", "Occupied"),], default="vacant")
    is_vacant = models.BooleanField(default=True, help_text="Is unit currently vacant?")
    is_verified = models.BooleanField(default=False, help_text="Has unit been verified?")
    maintenance_notes = models.TextField(blank=True, null=True, help_text="Maintenance related notes")
    rent_due_reminder = models.BooleanField(default=True, help_text="Enable rent due reminders?")
    agreement_expiry_reminder = models.BooleanField(default=True, help_text="Enable agreement expiry reminders?")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude coordinate")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ('owner', 'unit', 'building', 'address_line')
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['owner']),
        ]
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.latitude and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        if self.longitude and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError("Longitude must be between -180 and 180.")

    def __str__(self):
        return f"{self.unit} - {self.city}, {self.state}"

    @property
    def name(self):
        return self.building_name or self.unit

class Caretaker(models.Model):
    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='caretakers', db_index=True)
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
    start_date = models.DateField(blank=True, null=True, help_text="Start date of caretaker service", db_index=True)
    end_date = models.DateField(blank=True, null=True, help_text="End date of caretaker service")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ('unit', 'phone')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def clean(self):
        # Optional: Custom validation to ensure end_date > start_date
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")


class Renter(models.Model):

    class RenterStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        NOTICE_PERIOD = "notice_period", "Notice Period"
        REVOKED = "revoked", "Revoked"
        DEACTIVATED = "deactivated", "Deactivated"

    id = models.AutoField(primary_key=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='renters', db_index=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='renter_profile')
    name = models.CharField(max_length=100, help_text="Renter's full name")
    phone = models.CharField(validators=[phone_regex], max_length=15, help_text="Primary phone number")
    alternate_phone = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Alternate phone number")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, help_text="Emergency contact name")
    emergency_contact_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True, help_text="Emergency contact number")
    renter_image = models.ImageField(upload_to='renter_image/', blank=True, null=True, help_text="Photo of renter")
    id_proof = models.FileField(upload_to='id_proofs/renter/', help_text="Renter's ID proof document")
    rent_agreement = models.FileField(upload_to='agreements/', help_text="Rent agreement document")
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rent amount")
    start_date = models.DateField(help_text="Rental start date", db_index=True)
    end_date = models.DateField(null=True, blank=True, help_text="Rental end date")
    is_active = models.BooleanField(default=True, help_text="Is renter currently active?")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="For WhatsApp messages")
    rent_due_date = models.DateField(blank=True, null=True, default=date.today, help_text="Required for rent reminder")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Move in Date")
    late_payment_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    missed_rents = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True, null=True)

    is_agreement_revoked = models.BooleanField(default=False)
    revocation_reason = models.TextField(blank=True, null=True)
    revoked_by_owner = models.BooleanField(default=False)
    revoked_on = models.DateTimeField(blank=True, null=True)

    vacated_on = models.DateField(blank=True, null=True)  # Date tenant left

    status = models.CharField(max_length=20, choices=RenterStatus.choices, default=RenterStatus.ACTIVE)
    notice_start_date = models.DateField(null=True, blank=True)  # Optional, to track 1-month window

    final_invoice_path = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('unit', 'phone')
        ordering = ['-start_date']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    @property
    def property(self):
        return self.unit

    def __str__(self):
        return self.name


class RentRecord(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CHEQUE = 'cheque', 'Cheque'
        ONLINE = 'online', 'Online Transfer'
        OTHER = 'other', 'Other'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    id = models.AutoField(primary_key=True)
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE, related_name='rent_records', db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='rent_records_unit')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rent_records_owner', db_index=True)
    rent_month = models.DateField(help_text="Use first day of the month, e.g. 2025-05-01", db_index=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for rent")
    date_paid = models.DateField(help_text="Date when payment was made")
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, help_text="Payment status")
    payment_mode = models.CharField(max_length=20, choices=PaymentMode.choices, blank=True, null=True, help_text="Mode of payment")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(user_model=settings.AUTH_USER_MODEL)

    # Payout specific fields:
    payout_status = models.CharField(max_length=20, default="PENDING")  # or SUCCESS/FAILED
    payout_reference = models.CharField(max_length=100, null=True, blank=True)
    payout_retry_count = models.IntegerField(default=0)
    last_retry_on = models.DateTimeField(null=True, blank=True)
    # razorpay specific fields:
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_status = models.CharField(max_length=20, default="PENDING")

    # Auto-Resend Failed Payouts specific fields:
    payout_retries = models.IntegerField(default=0)
    last_payout_retry = models.DateTimeField(null=True, blank=True)

    # Auto-apply ₹/day late fee
    grace_days = models.PositiveIntegerField(default=3)
    late_fee = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)
    adjustment_reason = models.TextField(blank=True, null=True)


    # rent due reminder
    # msg = f"""📢 *Rent Due Reminder*
    # Hi {renter.name}, your rent of ₹{renter.rent_amount} for *{renter.property.name}* is due on *{renter.rent_due_date.strftime('%d %B')}*.
    # Please pay on time to avoid late fees. Thank you! 🙏
    # """
    rent_due_date = models.DateField(default=date.today)  # e.g., 1st of every month
    payment_link = models.URLField(null=True, blank=True)
    rent_due_day = models.IntegerField(default=5)  # Rent due every 5th of month


    is_active = models.BooleanField(default=True)

    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    invoice_pdf = models.FileField(upload_to="rent_invoices/", null=True, blank=True)

    class Meta:
        unique_together = ('renter', 'rent_month')
        ordering = ['-rent_month']

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative.")

        if self.date_paid < self.rent_month:
            raise ValidationError("Date paid cannot be before rent month.")

        if self.renter.unit != self.unit:
            raise ValidationError("Renter does not belong to the selected unit.")

    @property
    def amount(self):
        return self.amount_paid

    @property
    def payment_date(self):
        return self.date_paid

    @property
    def due_date(self):
        return self.rent_due_date

    @property
    def month(self):
        return self.rent_month.month

    @property
    def year(self):
        return self.rent_month.year

    def __str__(self):
        return f"{self.renter.name} - {self.rent_month.strftime('%B %Y')}"


class RentReminderLog(models.Model):
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, help_text="EXAMPLE: PRE, DUE, LATE")  
    sent_at = models.DateTimeField(auto_now_add=True)


class AgreementRevocationLog(models.Model):
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE)
    revoked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class UnitVacancy(models.Model):
    class Reason(models.TextChoices):
        RENOVATION = 'renovation', 'Renovation'
        CLEANING = 'cleaning', 'Cleaning'
        BETWEEN_RENTERS = 'between renters', 'Between Renters'
        LONG_TERM_VACANCY = 'long-term vacancy', 'Long-Term Vacancy'
        OTHER = 'other', 'Other'

    unit = models.OneToOneField(Unit, on_delete=models.CASCADE)
    reason = models.CharField(max_length=100, choices=Reason.choices)
    noted_on = models.DateField(auto_now_add=True)



class ArchivedRenter(models.Model):
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE)
    data = models.JSONField()
    agreement_pdf = models.FileField(upload_to="archived/agreements/")
    police_pdf = models.FileField(upload_to="archived/police/")
    property_images = models.JSONField(default=list)  # List of image paths
    final_invoice = models.FileField(upload_to="archived/final_invoice/")
    archived_at = models.DateTimeField(auto_now_add=True)




 # De-prioritized for now do not touch bellow models
class UnitDocument(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_index=True)
    renter = models.ForeignKey(Renter, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    document = models.FileField(upload_to='unit_documents/')
    file_hash = models.CharField(max_length=64, editable=False, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from .utils import generate_file_hash
        if self.document:
            hash_value = generate_file_hash(self.document)
            self.file_hash = hash_value

            # Check for duplicates
            if UnitDocument.objects.filter(file_hash=hash_value, unit=self.unit).exclude(pk=self.pk).exists():
                raise ValidationError("This document already exists for this unit.")


class UnitImage(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_index=True)
    renter = models.ForeignKey(Renter, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    image = models.ImageField(upload_to='unit_images/')
    image_hash = models.CharField(max_length=64, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from .utils import generate_file_hash
        if self.image:
            hash_value = generate_file_hash(self.image)
            self.image_hash = hash_value

            # Check for duplicates
            if UnitImage.objects.filter(image_hash=hash_value, unit=self.unit).exclude(pk=self.pk).exists():
                raise ValidationError("This image already exists for this unit.")


class RentAgreementDraft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE, db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='rent_agreement_draft')
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='auto_agreements/')

    class Meta:
        unique_together = ('renter', 'unit')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.renter.unit != self.unit:
            raise ValidationError("Renter must belong to the specified unit.")


class PoliceVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    renter = models.OneToOneField(Renter, on_delete=models.CASCADE, db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='police_verification')
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="rent_agreements/")

    class Meta:
        unique_together = ('renter', 'unit')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.renter.unit != self.unit:
            raise ValidationError("Renter must belong to the specified unit.")