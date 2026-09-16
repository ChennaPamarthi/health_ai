from django.db import models

from .medical_document import MedicalDocument
from .user import User


class Prescription(models.Model):

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    document = models.OneToOneField(
        MedicalDocument,
        on_delete=models.CASCADE,
        related_name="prescription",
        null=True,
        blank=True
    )

    doctor_name = models.CharField(
        max_length=150,
        blank=True
    )

    hospital_name = models.CharField(
        max_length=200,
        blank=True
    )

    diagnosis = models.TextField(
        blank=True
    )

    prescription_date = models.DateField(
        null=True,
        blank=True
    )

    review_date = models.DateField(
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

        db_table = "prescriptions"

        ordering = ["-created_at"]

    def __str__(self):

        return f"Prescription - {self.patient.full_name}"
