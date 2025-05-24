from django.contrib import admin
from django.utils.html import format_html
from .models import Property, Caretaker, Renter, RentRecord
from simple_history.admin import SimpleHistoryAdmin


# admin.site.site_header = "Wealth Concierge Admin"


# Inline admin for Caretaker inside Property (optional, remove if not needed)
class CaretakerInline(admin.TabularInline):
    model = Caretaker
    extra = 1
    readonly_fields = ('caretaker_image_thumbnail',)

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url)
        return "-"
    caretaker_image_thumbnail.short_description = "Caretaker Image"

# Inline admin for Renter inside Property (optional)
class RenterInline(admin.TabularInline):
    model = Renter
    extra = 1
    readonly_fields = ('renter_image_thumbnail',)

    def renter_image_thumbnail(self, obj):
        if obj.renter_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.renter_image.url)
        return "-"
    renter_image_thumbnail.short_description = "Renter Image"


@admin.register(Property)
class PropertyAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'title', 'owner', 'address_line', 'landmark', 'city', 'state', 'country', 
        'postal_code', 'whatsapp_number', 'property_type', 'property_image_thumbnail', 'is_vacant', 
        'is_verified', 'maintenance_notes', 'rent_due_reminder', 'agreement_expiry_reminder', 
        'latitude', 'longitude', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('title', 'city', 'owner__username')
    list_filter = ('property_type', 'is_vacant', 'is_verified')
    readonly_fields = ('created_at', 'updated_at', 'property_image_thumbnail')
    inlines = [CaretakerInline, RenterInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'title', 'property_type')
        }),
        ('Address', {
            'fields': ('address_line', 'landmark', 'city', 'state', 'country', 'postal_code', 'whatsapp_number',)
        }),
        ('Documents & Images', {
            'fields': ('property_image', 'property_image_thumbnail', 'id_proof')
        }),
        ('Status & Reminders', {
            'fields': ('is_vacant', 'is_verified', 'rent_due_reminder', 'agreement_expiry_reminder')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Additional Notes', {
            'fields': ('maintenance_notes', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def property_image_thumbnail(self, obj):
        if obj.property_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.property_image.url)
        return "-"
    property_image_thumbnail.short_description = 'Property Image Preview'


@admin.register(Caretaker)
class CaretakerAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'property', 'name', 'phone', 'alternate_phone', 'whatsapp_number', 'emergency_contact_name', 
        'emergency_contact_number', 'caretaker_image_thumbnail', 'address_line', 'landmark', 'city', 'state', 'country', 'postal_code', 
        'start_date', 'end_date', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at', 'caretaker_image_thumbnail')
    fieldsets = (
        ('Basic Info', {
            'fields': ('property', 'name', 'phone', 'alternate_phone', 'whatsapp_number')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number')
        }),
        ('Documents', {
            'fields': ('caretaker_image', 'caretaker_image_thumbnail', 'id_proof')
        }),
        ('Address', {
            'fields': ('address_line', 'landmark', 'city', 'state', 'country', 'postal_code')
        }),
        ('Dates & Notes', {
            'fields': ('start_date', 'end_date', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url)
        return "-"
    caretaker_image_thumbnail.short_description = 'Caretaker Image Preview'


@admin.register(Renter)
class RenterAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'property', 'name', 'phone', 'alternate_phone', 'whatsapp_number', 'emergency_contact_name', 
        'emergency_contact_number', 'renter_image_thumbnail', 'rent_amount', 
        'start_date', 'end_date', 'is_active', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'renter_image_thumbnail')
    fieldsets = (
        ('Basic Info', {
            'fields': ('property', 'name', 'phone', 'alternate_phone', 'whatsapp_number')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number')
        }),
        ('Documents', {
            'fields': ('renter_image', 'renter_image_thumbnail', 'id_proof', 'rent_agreement')
        }),
        ('Rental Details', {
            'fields': ('rent_amount', 'start_date', 'end_date', 'is_active')
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def renter_image_thumbnail(self, obj):
        if obj.renter_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.renter_image.url)
        return "-"
    renter_image_thumbnail.short_description = 'Renter Image Preview'


@admin.register(RentRecord)
class RentRecordAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'renter', 'property', 'rent_month', 'amount_paid', 'date_paid', 
        'payment_mode', 'remarks', 'created_at', 'updated_at'
    )
    search_fields = ('renter__name',)
    list_filter = ('rent_month',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Rent Info', {
            'fields': ('renter', 'property', 'rent_month', 'amount_paid', 'date_paid', 'payment_mode')
        }),
        ('Additional Info', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # Example custom action to bulk mark rent records as paid (optional)
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        updated_count = queryset.update(remarks="Paid")
        self.message_user(request, f"{updated_count} rent record(s) marked as Paid.")
    mark_as_paid.short_description = "Mark selected rent records as Paid"


from django.contrib import admin
from .models import (
    PropertyTaxRecord, SubscriptionPlan, UserSubscription,
    AddOnPurchase, PlanFeatureLimit, UsageLimit,
    RentAgreementDraft, PDFExportRecord,
    PropertyImage, PropertyDocument
)

@admin.register(PropertyTaxRecord)
class PropertyTaxRecordAdmin(admin.ModelAdmin):
    list_display = ('property', 'tax_year', 'amount', 'is_paid', 'payment_date', 'is_verified')
    list_filter = ('is_paid', 'is_verified', 'tax_year', 'payment_mode')
    search_fields = ('property__title', 'tax_year')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_price', 'yearly_price', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'is_yearly', 'tax_reminder_days_before', 'rent_reminder_days_before')
    search_fields = ('user__username', 'plan__name', 'rent_reminder_days_before')
    list_editable = ('tax_reminder_days_before',)
    readonly_fields = ('created_at', 'updated_at',)

@admin.register(AddOnPurchase)
class AddOnPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'amount', 'is_recurring', 'purchase_date')
    search_fields = ('user__username', 'name')

@admin.register(PlanFeatureLimit)
class PlanFeatureLimitAdmin(admin.ModelAdmin):
    list_display = ('plan', 'feature_key', 'value')
    list_filter = ('feature_key',)
    search_fields = ('plan__name', 'feature_key')

@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature_key', 'usage_count', 'updated_at')
    search_fields = ('user__username', 'feature_key')

@admin.register(RentAgreementDraft)
class RentAgreementDraftAdmin(admin.ModelAdmin):
    list_display = ('user', 'renter', 'generated_at')
    search_fields = ('user__username', 'renter__name')

@admin.register(PDFExportRecord)
class PDFExportRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'exported_at')
    search_fields = ('user__username', 'property__title')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'uploaded_at')
    search_fields = ('property__title',)

@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ('property', 'document', 'uploaded_at')
    search_fields = ('property__title',)