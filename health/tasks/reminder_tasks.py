from django.utils import timezone

from health.services.caregiver_service import CaregiverService
from health.services.notification_service import NotificationService
from health.services.reminder_service import ReminderService


class ReminderTask:
    """
    Coordinates the reminder workflow.
    """

    def __init__(self):
        self.reminder_service = ReminderService()
        self.notification_service = NotificationService()
        self.caregiver_service = CaregiverService()

    def run(self):
        """
        Execute one reminder cycle.
        """
        reminders = self.reminder_service.create_reminders()
        now = timezone.now()
        pending_reminders = self.reminder_service.get_pending_reminders().filter(
            status="Pending",
            reminder_datetime__lte=now,
        )

        sent = []
        for reminder in pending_reminders:
            self.notification_service.send_reminder(reminder)
            sent.append(self.reminder_service.mark_sent(reminder))

        escalated = self.caregiver_service.process_missed_reminders()

        return {
            "created": len(reminders),
            "sent": len(sent),
            "escalated": len(escalated),
            "status": "Success",
        }

