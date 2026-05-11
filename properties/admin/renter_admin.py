from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from ..models import Renter


@admin.register(Renter)
class RenterAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number',
        'emergency_contact_name', 'emergency_contact_number', 'renter_image_thumbnail',
        'rent_amount', 'start_date', 'end_date', 'is_active', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'renter_image_thumbnail')
    fieldsets = (
        ('Basic Info', {'fields': ('unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_number')}),
        ('Documents', {'fields': ('renter_image', 'renter_image_thumbnail', 'id_proof', 'rent_agreement')}),
        ('Rental Details', {'fields': ('rent_amount', 'start_date', 'end_date', 'is_active')}),
        ('Additional Info', {'fields': ('notes',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def renter_image_thumbnail(self, obj):
        if obj.renter_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.renter_image.url)
        return "-"
    renter_image_thumbnail.short_description = 'Renter Image Preview'
