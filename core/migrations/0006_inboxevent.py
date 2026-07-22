import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_outboxevent"),
    ]

    operations = [
        migrations.CreateModel(
            name="InboxEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "event_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("event_type", models.CharField(db_index=True, max_length=255)),
                ("aggregate_id", models.UUIDField(db_index=True)),
                ("aggregate_type", models.CharField(db_index=True, max_length=100)),
                ("payload", models.JSONField()),
                ("headers", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("RECEIVED", "RECEIVED"),
                            ("PROCESSING", "PROCESSING"),
                            ("PROCESSED", "PROCESSED"),
                            ("FAILED", "FAILED"),
                            ("DEAD_LETTER", "DEAD_LETTER"),
                        ],
                        db_index=True,
                        default="RECEIVED",
                        max_length=20,
                    ),
                ),
                ("received_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("retry_count", models.PositiveIntegerField(default=0)),
                ("max_retry", models.PositiveIntegerField(default=6)),
                (
                    "next_retry_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "inbox_event",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="inboxevent",
            index=models.Index(
                fields=["event_id"],
                name="inbox_event_event_id_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="inboxevent",
            index=models.Index(
                fields=["status", "received_at"],
                name="inbox_event_status_received_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="inboxevent",
            index=models.Index(
                fields=["event_type", "aggregate_id"],
                name="inbox_event_type_aggregate_idx",
            ),
        ),
    ]
