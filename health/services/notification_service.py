import logging
from django.utils import timezone

from django.conf import settings

from health.models import NotificationEvent, Reminder

from .email_service import EmailService
from .sms_service import SMSService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Handles sending reminder notifications.
    """

    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()

    def _build_message(self, reminder: Reminder):
        patient = reminder.schedule.medicine.prescription.patient
        medicine = reminder.schedule.medicine
        return (
            f"Reminder for {patient.full_name}: "
            f"Take {medicine.medicine_name}"
            f" ({medicine.dosage or 'No dosage'}) at "
            f"{reminder.schedule.reminder_time.strftime('%H:%M')}."
        )

    @staticmethod
    def _should_send_email(patient):
        preference = getattr(patient, "notification_preference", "email")
        enabled = getattr(patient, "enable_notifications", True)
        return enabled and preference in {"email", "email_sms"}

    @staticmethod
    def _should_send_sms(patient):
        preference = getattr(patient, "notification_preference", "email")
        enabled = getattr(patient, "enable_notifications", True)
        return enabled and preference in {"sms", "email_sms"}

    def _send_email(self, patient, subject, body):
        if not getattr(patient, "email", ""):
            return {"success": False, "message": "Patient email is missing."}

        html_body = f"<p>{body}</p>"
        return self.email_service.send_email(
            subject=subject,
            html_body=html_body,
            recipient_list=[patient.email],
            text_body=body,
        )

    def _send_sms(self, patient, body):
        if not getattr(settings, "SMS_ENABLED", False):
            return {"success": False, "message": "SMS notifications are disabled."}

        if not getattr(patient, "phone", ""):
            return {"success": False, "message": "Patient phone number is missing."}

        return self.sms_service.send_sms(patient.phone, body)

    def send_reminder(self, reminder: Reminder):
        """
        Send a medicine reminder.
        """
        patient = reminder.schedule.medicine.prescription.patient
        message = self._build_message(reminder)

        email_result = {"success": False, "message": "Email not selected."}
        sms_result = {"success": False, "message": "SMS not selected."}

        if self._should_send_email(patient):
            email_result = self._send_email(
                patient,
                subject="Medicine reminder",
                body=message,
            )
            NotificationEvent.objects.create(
                reminder=reminder,
                recipient_user=patient,
                recipient_label=patient.full_name,
                channel="email",
                status="Delivered" if email_result.get("success") else "Failed",
                delivered_at=timezone.now() if email_result.get("success") else None,
                email_message_id=email_result.get("message", ""),
                error_message="" if email_result.get("success") else email_result.get("message", ""),
            )

        if self._should_send_sms(patient):
            sms_result = self._send_sms(patient, message)
            NotificationEvent.objects.create(
                reminder=reminder,
                recipient_user=patient,
                recipient_label=patient.full_name,
                channel="sms",
                status="Delivered" if sms_result.get("success") else "Failed",
                delivered_at=timezone.now() if sms_result.get("success") else None,
                twilio_sid=sms_result.get("sid", ""),
                error_message="" if sms_result.get("success") else sms_result.get("message", ""),
            )

        logger.info(message)

        return {
            "success": True,
            "message": message,
            "email": email_result,
            "sms": sms_result,
        }

    def send_missed_alert(self, reminder: Reminder):
        patient = reminder.schedule.medicine.prescription.patient
        medicine = reminder.schedule.medicine
        message = (
            f"ALERT: {patient.full_name} has not logged {medicine.medicine_name} "
            f"scheduled at {reminder.schedule.reminder_time.strftime('%H:%M')}."
        )

        email_result = {"success": False, "message": "Email not selected."}
        sms_result = {"success": False, "message": "SMS not selected."}

        if self._should_send_email(patient):
            email_result = self._send_email(
                patient,
                subject="Missed medicine alert",
                body=message,
            )
            NotificationEvent.objects.create(
                reminder=reminder,
                recipient_user=patient,
                recipient_label=patient.full_name,
                channel="email",
                status="Delivered" if email_result.get("success") else "Failed",
                delivered_at=timezone.now() if email_result.get("success") else None,
                error_message="" if email_result.get("success") else email_result.get("message", ""),
            )

        if self._should_send_sms(patient):
            sms_result = self._send_sms(patient, message)
            NotificationEvent.objects.create(
                reminder=reminder,
                recipient_user=patient,
                recipient_label=patient.full_name,
                channel="sms",
                status="Delivered" if sms_result.get("success") else "Failed",
                delivered_at=timezone.now() if sms_result.get("success") else None,
                twilio_sid=sms_result.get("sid", ""),
                error_message="" if sms_result.get("success") else sms_result.get("message", ""),
            )

        logger.warning(message)

        return {
            "success": True,
            "message": message,
            "email": email_result,
            "sms": sms_result,
        }

    def send_bulk(self, reminders):
        """
        Send multiple reminders.
        """
        return [self.send_reminder(reminder) for reminder in reminders]
