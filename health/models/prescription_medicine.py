from django.db import models

from .prescription import Prescription


class PrescriptionMedicine(models.Model):

    FOOD_CHOICES = [

        ("Before Food", "Before Food"),

        ("After Food", "After Food"),

        ("With Food", "With Food"),

        ("Anytime", "Anytime"),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="medicines"
    )

    medicine_name = models.CharField(
        max_length=200
    )

    strength = models.CharField(
        max_length=100,
        blank=True
    )

    dosage = models.CharField(
        max_length=100,
        blank=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    frequency = models.JSONField(
        default=list,
        blank=True
    )

    duration = models.CharField(
        max_length=100,
        blank=True
    )

    food_instruction = models.CharField(
        max_length=30,
        choices=FOOD_CHOICES,
        default="After Food"
    )

    special_instruction = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "prescription_medicines"

        ordering = ["medicine_name"]

    def __str__(self):

        return self.medicine_name