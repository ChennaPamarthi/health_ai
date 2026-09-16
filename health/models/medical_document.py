from django.db import models

from .user import User


class MedicalDocument(models.Model):

    DOCUMENT_TYPES = [

        ("Prescription", "Prescription"),

        ("Blood Report", "Blood Report"),

        ("MRI", "MRI"),

        ("ECG", "ECG"),

        ("X-Ray", "X-Ray"),

        ("Appointment", "Appointment"),

        ("Other", "Other"),
    ]

    STATUS_CHOICES = [

        ("Uploaded", "Uploaded"),

        ("Processing", "Processing"),

        ("Completed", "Completed"),

        ("Failed", "Failed"),
    ]

    CLASSIFICATION_CHOICES = [
        ("printed", "Printed"),
        ("handwritten", "Handwritten"),
        ("unknown", "Unknown"),
    ]

    patient = models.ForeignKey(

        User,

        on_delete=models.CASCADE,

        related_name="documents"
    )

    title = models.CharField(

        max_length=200,

        blank=True
    )

    description = models.TextField(

        blank=True
    )

    document_type = models.CharField(

        max_length=50,

        choices=DOCUMENT_TYPES
    )

    file = models.FileField(

        upload_to="documents/"
    )

    extracted_text = models.TextField(

        blank=True
    )

    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        default="unknown"
    )

    classification_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=0
    )

    ocr_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=0
    )

    vision_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=0
    )

    needs_review = models.BooleanField(
        default=False
    )

    structured_payload = models.JSONField(
        default=dict,
        blank=True
    )

    status = models.CharField(

        max_length=20,

        choices=STATUS_CHOICES,

        default="Uploaded"
    )

    uploaded_at = models.DateTimeField(

        auto_now_add=True
    )

    updated_at = models.DateTimeField(

        auto_now=True
    )

    class Meta:

        db_table = "medical_documents"

        ordering = ["-uploaded_at"]

    def __str__(self):

        return f"{self.document_type} - {self.patient.full_name}"
