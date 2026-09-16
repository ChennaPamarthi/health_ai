from datetime import timedelta

from django.utils import timezone

from health.models import Caregiver, NotificationEvent, Reminder

from .notification_service import NotificationService


class CaregiverService:
    """
    Handles caregiver escalation for missed medicine reminders.
    """

    ESCALATION_AFTER_MINUTES = 10

    def __init__(self):
        self.notification_service = NotificationService()

    def get_escalation_due_reminders(self):
        cutoff_time = timezone.now() - timedelta(minutes=self.ESCALATION_AFTER_MINUTES)
        return (
            Reminder.objects.filter(
                status__in=["Sent", "Delivered"],
                response_status="Pending",
                sent_at__lte=cutoff_time,
            )
            .select_related(
                "schedule",
                "schedule__medicine",
                "schedule__medicine__prescription",
                "schedule__medicine__prescription__patient",
            )
        )

    def get_caregivers(self, patient):
        return Caregiver.objects.filter(
            patient=patient,
            enable_notifications=True,
        ).order_by("-is_primary", "name")

    def notify_caregivers(self, reminder):
        patient = reminder.schedule.medicine.prescription.patient
        medicine = reminder.schedule.medicine
        caregivers = self.get_caregivers(patient)
        results = []

        patient_result = self.notification_service.send_missed_alert(reminder)
        results.append(
            {
                "patient_id": patient.id,
                "patient": patient_result,
            }
        )

        for caregiver in caregivers:
            body = (
                f"Patient has not confirmed today's medicine.\n"
                f"Patient: {patient.full_name}\n"
                f"Medicine: {medicine.medicine_name}\n"
                f"Time: {reminder.schedule.reminder_time.strftime('%H:%M')}\n"
                f"Please contact the patient."
            )

            email_result = {"success": False, "message": "Email not requested."}
            sms_result = {"success": False, "message": "SMS not requested."}

            preference = caregiver.notification_preference
            if preference in {"email", "email_sms"} and caregiver.email:
                email_result = self.notification_service.email_service.send_email(
                    subject="Missed medicine reminder",
                    html_body=f"<p>{body.replace(chr(10), '<br>')}</p>",
                    recipient_list=[caregiver.email],
                    text_body=body,
                )

            if preference in {"sms", "email_sms"} and caregiver.phone:
                sms_result = self.notification_service.sms_service.send_sms(caregiver.phone, body)

            if preference in {"email", "email_sms"}:
                NotificationEvent.objects.create(
                    reminder=reminder,
                    recipient_user=caregiver.patient,
                    recipient_label=caregiver.name,
                    channel="email",
                    status="Escalated" if email_result.get("success") else "Failed",
                    delivered_at=timezone.now() if email_result.get("success") else None,
                    escalated_at=timezone.now() if email_result.get("success") else None,
                    error_message="" if email_result.get("success") else email_result.get("message", ""),
                )

            if preference in {"sms", "email_sms"}:
                NotificationEvent.objects.create(
                    reminder=reminder,
                    recipient_user=caregiver.patient,
                    recipient_label=caregiver.name,
                    channel="sms",
                    status="Escalated" if sms_result.get("success") else "Failed",
                    delivered_at=timezone.now() if sms_result.get("success") else None,
                    escalated_at=timezone.now() if sms_result.get("success") else None,
                    twilio_sid=sms_result.get("sid", ""),
                    error_message="" if sms_result.get("success") else sms_result.get("message", ""),
                )

            results.append(
                {
                    "caregiver_id": caregiver.id,
                    "email": email_result,
                    "sms": sms_result,
                }
            )

        reminder.escalated_at = timezone.now()
        reminder.status = "Failed"
        reminder.response_status = "Missed"
        reminder.save(update_fields=["escalated_at", "status", "response_status"])

        return results

    def process_missed_reminders(self):
        reminders = self.get_escalation_due_reminders()
        results = []
        for reminder in reminders:
            results.append(self.notify_caregivers(reminder))
        return results
