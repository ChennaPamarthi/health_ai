from django.db import models


class User(models.Model):

    NOTIFICATION_PREFERENCE_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("email_sms", "Email + SMS"),
    ]

    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("caregiver", "Caregiver"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ]

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    full_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="patient"
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    emergency_contact = models.CharField(
        max_length=15,
        blank=True
    )

    primary_email = models.EmailField(
        blank=True
    )

    primary_phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    notification_preference = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PREFERENCE_CHOICES,
        default="email"
    )

    enable_notifications = models.BooleanField(
        default=True
    )

    timezone = models.CharField(
        max_length=64,
        default="Asia/Kolkata"
    )

    reminder_interval_minutes = models.PositiveIntegerField(
        default=15
    )

    reminder_retry_count = models.PositiveIntegerField(
        default=1
    )

    reminder_sound_enabled = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "users"

        ordering = ["full_name"]

    def __str__(self):

        return self.full_name
