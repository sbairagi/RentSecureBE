from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from django.contrib import admin
from .models import (RentAgreementDraft, UnitImage, UnitDocument, Unit,
                     Caretaker, Renter, RentRecord)

admin.site.site_header = "Wealth Concierge Admin"


# Inline admin for Caretaker inside unit (optional, remove if not needed)
class CaretakerInline(admin.TabularInline):
    model = Caretaker
    extra = 1
    readonly_fields = ('caretaker_image_thumbnail',)

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url)
        return "-"
    caretaker_image_thumbnail.short_description = "Caretaker Image"

# Inline admin for Renter inside unit (optional)
class RenterInline(admin.TabularInline):
    model = Renter
    extra = 1
    readonly_fields = ('renter_image_thumbnail',)

    def renter_image_thumbnail(self, obj):
        if obj.renter_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.renter_image.url)
        return "-"
    renter_image_thumbnail.short_description = "Renter Image"


@admin.register(Unit)
class UnitAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'building_name', 'unit', 'owner', 'address_line', 'landmark', 'city', 'state', 'country', 
        'postal_code', 'unit_type', 'unit_image_thumbnail', 'is_vacant', 
        'is_verified', 'maintenance_notes', 'rent_due_reminder', 'agreement_expiry_reminder', 
        'latitude', 'longitude', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('building__name', 'building_name', 'unit', 'city', 'owner__username')
    list_filter = ('unit_type', 'is_vacant', 'is_verified')
    readonly_fields = ('created_at', 'updated_at', 'unit_image_thumbnail')
    inlines = [CaretakerInline, RenterInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'building__name', 'building_name', 'unit', 'unit_type')
        }),
        ('Address', {
            'fields': ('address_line', 'landmark', 'city', 'state', 'country', 'postal_code')
        }),
        ('Documents & Images', {
            'fields': ('unit_image', 'unit_image_thumbnail', 'id_proof')
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

    def unit_image_thumbnail(self, obj):
        if obj.unit_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.unit_image.url)
        return "-"
    unit_image_thumbnail.short_description = 'Unit Image Preview'


@admin.register(Caretaker)
class CaretakerAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number', 'emergency_contact_name', 
        'emergency_contact_number', 'caretaker_image_thumbnail', 'address_line', 'landmark', 'city', 'state', 'country', 'postal_code', 
        'start_date', 'end_date', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at', 'caretaker_image_thumbnail')
    fieldsets = (
        ('Basic Info', {
            'fields': ('unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number')
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
        'id', 'unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number', 'emergency_contact_name', 
        'emergency_contact_number', 'renter_image_thumbnail', 'rent_amount', 
        'start_date', 'end_date', 'is_active', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'renter_image_thumbnail')
    fieldsets = (
        ('Basic Info', {
            'fields': ('unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number')
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
        'id', 'renter', 'unit', 'rent_month', 'amount_paid', 'date_paid', 
        'payment_mode', 'remarks', 'created_at', 'updated_at',
        'grace_days', 'late_fee'
    )
    search_fields = ('renter__name',)
    list_filter = ('rent_month',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Rent Info', {
            'fields': ('renter', 'unit', 'rent_month', 'amount_paid', 'date_paid', 'payment_mode')
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









#De-priritize don't touch the below code

@admin.register(RentAgreementDraft)
class RentAgreementDraftAdmin(admin.ModelAdmin):
    list_display = ('user', 'renter', 'generated_at')
    search_fields = ('user__username', 'renter__name')


@admin.register(UnitImage)
class UnitImageAdmin(admin.ModelAdmin):
    list_display = ('unit', 'image', 'uploaded_at')
    search_fields = ('unit__unit',)

@admin.register(UnitDocument)
class UnitDocumentAdmin(admin.ModelAdmin):
    list_display = ('unit', 'document', 'uploaded_at')
    search_fields = ('unit__unit',)