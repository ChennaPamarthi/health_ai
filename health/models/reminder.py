from django.db import models

from .medicine_schedule import MedicineSchedule


class Reminder(models.Model):

    STATUS_CHOICES = [

        ("Pending", "Pending"),

        ("Sent", "Sent"),

        ("Delivered", "Delivered"),

        ("Read", "Read"),

        ("Completed", "Completed"),

        ("Failed", "Failed"),
    ]

    RESPONSE_CHOICES = [
        ("Pending", "Pending"),
        ("Taken", "Taken"),
        ("Skipped", "Skipped"),
        ("Snooze", "Snooze"),
        ("Missed", "Missed"),
    ]

    schedule = models.ForeignKey(
        MedicineSchedule,
        on_delete=models.CASCADE,
        related_name="reminders"
    )

    reminder_datetime = models.DateTimeField()

    message = models.TextField()

    response_status = models.CharField(
        max_length=20,
        choices=RESPONSE_CHOICES,
        default="Pending"
    )

    reminder_key = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    escalated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "reminders"

        ordering = [
            "-reminder_datetime"
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "reminder_datetime"],
                name="unique_reminder_schedule_datetime",
            )
        ]

    def __str__(self):

        return (
            f"{self.schedule.medicine.medicine_name} "
            f"- {self.reminder_datetime}"
        )
