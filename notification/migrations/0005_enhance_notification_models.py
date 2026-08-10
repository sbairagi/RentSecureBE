# Migration to enhance notification models with production-grade fields

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("notification", "0004_whatsapp_log_retry_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="action_label",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="notification",
            name="action_url",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="notification",
            name="archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="notification",
            name="channels",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="notification",
            name="data",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="notification",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="notification",
            name="image_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("rent_due", "Rent Due"),
                    ("payment_success", "Payment Success"),
                    ("payment_failed", "Payment Failed"),
                    ("agreement_expiry", "Agreement Expiring"),
                    ("agreement_signed", "Agreement Signed"),
                    ("maintenance_created", "Maintenance Created"),
                    ("maintenance_update", "Maintenance Updated"),
                    ("visitor_request", "Visitor Request"),
                    ("visitor_approved", "Visitor Approved"),
                    ("subscription_expiry", "Subscription Expiring"),
                    ("subscription_expired", "Subscription Expired"),
                    ("document_shared", "Document Shared"),
                    ("system_announcement", "System Alert"),
                    ("payout_success", "Payout Success"),
                    ("payout_failed", "Payout Failed"),
                    ("renter_status_change", "Renter Status Change"),
                    ("itr_reminder", "ITR Reminder"),
                    ("tax_reminder", "Tax Reminder"),
                    ("extra_charge_reminder", "Extra Charge Reminder"),
                ],
                default="system_announcement",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="priority",
            field=models.CharField(
                choices=[
                    ("low", "Low"),
                    ("medium", "Medium"),
                    ("high", "High"),
                    ("urgent", "Urgent"),
                ],
                default="medium",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="read_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="notification",
            name="resource_id",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="notification",
            name="resource_type",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterModelOptions(
            name="notification",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["user", "is_read", "created_at"],
                name="notification_user_read_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["user", "notification_type"],
                name="notification_user_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["user", "resource_type", "resource_id"],
                name="notification_user_resource_idx",
            ),
        ),
        migrations.AlterField(
            model_name="devicetoken",
            name="platform",
            field=models.CharField(
                choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web")],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="device_id",
            field=models.CharField(blank=True, max_length="255"),
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="fcm_token",
            field=models.CharField(blank=True, max_length="255"),
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="last_used",
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
