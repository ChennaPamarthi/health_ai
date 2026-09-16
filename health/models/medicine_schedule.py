from django.db import models

from .prescription_medicine import PrescriptionMedicine


class MedicineSchedule(models.Model):

    STATUS_CHOICES = [

        ("Active", "Active"),

        ("Paused", "Paused"),

        ("Completed", "Completed"),
    ]

    medicine = models.ForeignKey(
        PrescriptionMedicine,
        on_delete=models.CASCADE,
        related_name="schedules"
    )

    day_number = models.PositiveIntegerField(
        default=1
    )

    reminder_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active"
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    is_enabled = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "medicine_schedules"

        ordering = [
            "reminder_time"
        ]

    def __str__(self):

        return f"{self.medicine.medicine_name} - {self.reminder_time}"