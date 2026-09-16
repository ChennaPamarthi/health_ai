from django.db import models

from .reminder import Reminder
from .user import User


class NotificationEvent(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Delivered", "Delivered"),
        ("Failed", "Failed"),
        ("Opened", "Opened"),
        ("Taken", "Taken"),
        ("Skipped", "Skipped"),
        ("Snooze", "Snooze"),
        ("Escalated", "Escalated"),
    ]

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("manual", "Manual"),
    ]

    reminder = models.ForeignKey(
        Reminder,
        on_delete=models.CASCADE,
        related_name="notification_events",
    )
    recipient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_events",
    )
    recipient_label = models.CharField(max_length=150, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    skipped_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    twilio_sid = models.CharField(max_length=100, blank=True)
    email_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reminder_id} - {self.channel} - {self.status}"
