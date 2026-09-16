from django.db import models

from .user import User


class Caregiver(models.Model):
    NOTIFICATION_PREFERENCE_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("email_sms", "Email + SMS"),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="caregivers"
    )
    name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notification_preference = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PREFERENCE_CHOICES,
        default="email",
    )
    enable_notifications = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "caregivers"
        ordering = ["-is_primary", "name"]

    def __str__(self):
        return f"{self.name} ({self.patient.full_name})"

