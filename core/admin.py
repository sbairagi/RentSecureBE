from django.contrib import admin

from core.events.outbox import admin as _outbox_admin  # noqa: F401

from .models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    User,
    UserSubscription,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "full_name",
        "email",
        "is_investor",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "full_name", "email", "phone")
    list_filter = ("is_investor", "is_staff", "is_active")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_price", "yearly_price", "is_active")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "start_date",
        "end_date",
        "is_active",
        "is_yearly",
        "tax_reminder_days_before",
        "rent_reminder_days_before",
    )
    search_fields = ("user__username", "plan__name", "rent_reminder_days_before")
    list_editable = ("tax_reminder_days_before",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(AddOnPurchase)
class AddOnPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "amount", "is_recurring", "purchase_date")
    search_fields = ("user__username", "name")


@admin.register(PlanFeatureLimit)
class PlanFeatureLimitAdmin(admin.ModelAdmin):
    list_display = ("plan", "feature_key", "value")
    list_filter = ("feature_key",)
    search_fields = ("plan__name", "feature_key")


@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "feature_key", "usage_count", "updated_at")
    search_fields = ("user__username", "feature_key")
