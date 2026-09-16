from django.db import models

from .medical_document import MedicalDocument
from .user import User


class MedicalReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ("Blood Report", "Blood Report"),
        ("MRI", "MRI"),
        ("ECG", "ECG"),
        ("X-Ray", "X-Ray"),
        ("Other", "Other"),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="medical_reports",
    )

    document = models.OneToOneField(
        MedicalDocument,
        on_delete=models.CASCADE,
        related_name="medical_report",
    )

    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
    )

    report_title = models.CharField(
        max_length=200,
        blank=True,
    )

    summary = models.TextField(
        blank=True,
    )

    findings = models.TextField(
        blank=True,
    )

    recommendations = models.TextField(
        blank=True,
    )

    report_date = models.DateField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "medical_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} - {self.patient.full_name}"
