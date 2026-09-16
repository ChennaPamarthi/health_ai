from django.db import models

from .user import User


class HealthJournal(models.Model):

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="health_journals"
    )

    recorded_at = models.DateTimeField(
        auto_now_add=True
    )

    blood_pressure = models.CharField(
        max_length=30,
        blank=True
    )

    blood_sugar = models.CharField(
        max_length=30,
        blank=True
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    oxygen_level = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    pulse_rate = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    symptoms = models.TextField(
        blank=True
    )

    mood = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    class Meta:

        db_table = "health_journals"

        ordering = [
            "-recorded_at"
        ]

    def __str__(self):

        return (
            f"{self.patient.full_name} - "
            f"{self.recorded_at.date()}"
        )