from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from ..models import Caretaker


@admin.register(Caretaker)
class CaretakerAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number',
        'emergency_contact_name', 'emergency_contact_number', 'caretaker_image_thumbnail',
        'address_line', 'landmark', 'city', 'state', 'country', 'postal_code',
        'start_date', 'end_date', 'notes', 'created_at', 'updated_at'
    )
    search_fields = ('name', 'phone')
    list_filter = ('start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at', 'caretaker_image_thumbnail')
    fieldsets = (
        ('Basic Info', {'fields': ('unit', 'name', 'phone', 'alternate_phone', 'whatsapp_number')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_number')}),
        ('Documents', {'fields': ('caretaker_image', 'caretaker_image_thumbnail', 'id_proof')}),
        ('Address', {'fields': ('address_line', 'landmark', 'city', 'state', 'country', 'postal_code')}),
        ('Dates & Notes', {'fields': ('start_date', 'end_date', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def caretaker_image_thumbnail(self, obj):
        if obj.caretaker_image:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.caretaker_image.url)
        return "-"
    caretaker_image_thumbnail.short_description = 'Caretaker Image Preview'
