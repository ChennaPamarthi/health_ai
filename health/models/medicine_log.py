from django.db import models

from .medicine_schedule import MedicineSchedule


class MedicineLog(models.Model):

    STATUS_CHOICES = [

        ("Pending", "Pending"),

        ("Taken", "Taken"),

        ("Skipped", "Skipped"),

        ("Snooze", "Snooze"),

        ("Missed", "Missed"),
    ]

    schedule = models.ForeignKey(
        MedicineSchedule,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    scheduled_datetime = models.DateTimeField()

    taken_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    reminder_sent = models.BooleanField(
        default=False
    )

    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "medicine_logs"

        ordering = [
            "-scheduled_datetime"
        ]

    def __str__(self):

        return (
            f"{self.schedule.medicine.medicine_name} "
            f"- {self.status}"
        )
