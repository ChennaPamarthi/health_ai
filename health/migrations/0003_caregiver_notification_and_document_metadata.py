# Generated manually to support caregiver, notification tracking, and document metadata updates.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("health", "0002_medical_report"),
    ]

    operations = [
        migrations.CreateModel(
            name="Caregiver",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("relationship", models.CharField(blank=True, max_length=100)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                (
                    "notification_preference",
                    models.CharField(
                        choices=[("email", "Email"), ("sms", "SMS"), ("email_sms", "Email + SMS")],
                        default="email",
                        max_length=20,
                    ),
                ),
                ("enable_notifications", models.BooleanField(default=True)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="caregivers",
                        to="health.user",
                    ),
                ),
            ],
            options={
                "db_table": "caregivers",
                "ordering": ["-is_primary", "name"],
            },
        ),
        migrations.CreateModel(
            name="NotificationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "recipient_label",
                    models.CharField(blank=True, max_length=150),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("email", "Email"), ("sms", "SMS"), ("manual", "Manual")],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "Pending"),
                            ("Delivered", "Delivered"),
                            ("Failed", "Failed"),
                            ("Opened", "Opened"),
                            ("Taken", "Taken"),
                            ("Skipped", "Skipped"),
                            ("Snooze", "Snooze"),
                            ("Escalated", "Escalated"),
                        ],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("opened_at", models.DateTimeField(blank=True, null=True)),
                ("taken_at", models.DateTimeField(blank=True, null=True)),
                ("skipped_at", models.DateTimeField(blank=True, null=True)),
                ("escalated_at", models.DateTimeField(blank=True, null=True)),
                ("twilio_sid", models.CharField(blank=True, max_length=100)),
                ("email_message_id", models.CharField(blank=True, max_length=255)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recipient_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notification_events",
                        to="health.user",
                    ),
                ),
                (
                    "reminder",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_events",
                        to="health.reminder",
                    ),
                ),
            ],
            options={
                "db_table": "notification_events",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="user",
            name="primary_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="user",
            name="primary_phone_number",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="notification_preference",
            field=models.CharField(
                choices=[("email", "Email"), ("sms", "SMS"), ("email_sms", "Email + SMS")],
                default="email",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="enable_notifications",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="timezone",
            field=models.CharField(default="Asia/Kolkata", max_length=64),
        ),
        migrations.AddField(
            model_name="user",
            name="reminder_interval_minutes",
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="user",
            name="reminder_retry_count",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="user",
            name="reminder_sound_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="classification",
            field=models.CharField(
                choices=[("printed", "Printed"), ("handwritten", "Handwritten"), ("unknown", "Unknown")],
                default="unknown",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="classification_confidence",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="ocr_confidence",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="vision_confidence",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="needs_review",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="medicaldocument",
            name="structured_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="prescription",
            name="document",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prescription",
                to="health.medicaldocument",
            ),
        ),
        migrations.AlterField(
            model_name="medicinelog",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Taken", "Taken"),
                    ("Skipped", "Skipped"),
                    ("Snooze", "Snooze"),
                    ("Missed", "Missed"),
                ],
                default="Pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="reminder",
            name="response_status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Taken", "Taken"),
                    ("Skipped", "Skipped"),
                    ("Snooze", "Snooze"),
                    ("Missed", "Missed"),
                ],
                default="Pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="reminder",
            name="reminder_key",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="reminder",
            name="escalated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reminder",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="reminder",
            constraint=models.UniqueConstraint(
                fields=("schedule", "reminder_datetime"),
                name="unique_reminder_schedule_datetime",
            ),
        ),
    ]
