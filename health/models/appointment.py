from django.db import models

from .user import User


class Appointment(models.Model):

    STATUS_CHOICES = [

        ("Upcoming", "Upcoming"),

        ("Completed", "Completed"),

        ("Cancelled", "Cancelled"),

        ("Missed", "Missed"),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    doctor_name = models.CharField(
        max_length=150
    )

    hospital_name = models.CharField(
        max_length=200,
        blank=True
    )

    department = models.CharField(
        max_length=100,
        blank=True
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    purpose = models.TextField(
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Upcoming"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "appointments"

        ordering = [
            "appointment_date",
            "appointment_time"
        ]

    def __str__(self):

        return (
            f"{self.patient.full_name} - "
            f"{self.doctor_name}"
        )