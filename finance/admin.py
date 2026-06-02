from django.contrib import admin

from .models import CAProfile, TaxSubmissionToCA

# @admin.register(TaxFilingSummary)
# class TaxFilingSummaryAdmin(admin.ModelAdmin):
#     list_display = ('user', 'financial_year', 'created_at')


@admin.register(CAProfile)
class CAProfileAdmin(admin.ModelAdmin):
    list_display = ("firm_name", "contact_email", "phone", "verified")
    list_filter = ("verified",)


@admin.register(TaxSubmissionToCA)
class TaxSubmissionToCAAdmin(admin.ModelAdmin):
    list_display = ("sent_to_email", "sent_at")
