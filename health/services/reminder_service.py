from datetime import datetime

from django.utils import timezone

from health.models import MedicineLog, MedicineSchedule, Reminder


class ReminderService:
    """
    Service responsible for generating
    and updating medicine reminders.
    """

    def get_due_schedules(self):
        now = timezone.localtime()
        current_time = now.time().replace(second=0, microsecond=0)
        today = now.date()

        return (
            MedicineSchedule.objects.filter(
                status="Active",
                is_enabled=True,
                start_date__lte=today,
                reminder_time=current_time,
            )
            .select_related(
                "medicine",
                "medicine__prescription",
                "medicine__prescription__patient",
            )
        )

    def create_reminders(self):
        schedules = self.get_due_schedules()
        reminders = []
        today = timezone.localdate()

        for schedule in schedules:
            reminder_datetime = timezone.make_aware(
                datetime.combine(today, schedule.reminder_time),
                timezone.get_current_timezone(),
            )

            reminder, created = Reminder.objects.get_or_create(
                schedule=schedule,
                reminder_datetime=reminder_datetime,
                defaults={
                    "message": (
                        f"Take {schedule.medicine.medicine_name} "
                        f"at {schedule.reminder_time.strftime('%H:%M')}"
                    ),
                    "status": "Pending",
                    "response_status": "Pending",
                    "reminder_key": f"{schedule_id_key(schedule, reminder_datetime)}",
                },
            )

            if created:
                reminders.append(reminder)

        return reminders

    def get_pending_reminders(self):
        return Reminder.objects.filter(
            status__in=["Pending", "Sent"],
            response_status="Pending",
        )

    def mark_sent(self, reminder):
        reminder.status = "Sent"
        reminder.delivered_at = timezone.now()
        reminder.sent_at = timezone.now()
        reminder.save(update_fields=["status", "delivered_at", "sent_at"])
        return reminder

    def mark_taken(self, reminder):
        reminder.response_status = "Taken"
        reminder.status = "Completed"
        reminder.completed_at = timezone.now()
        reminder.save(update_fields=["response_status", "status", "completed_at"])
        return reminder

    def mark_skipped(self, reminder):
        reminder.response_status = "Skipped"
        reminder.status = "Delivered"
        reminder.save(update_fields=["response_status", "status"])
        return reminder

    def mark_snoozed(self, reminder):
        reminder.response_status = "Snooze"
        reminder.status = "Sent"
        reminder.save(update_fields=["response_status", "status"])
        return reminder

    def mark_missed(self, reminder):
        reminder.response_status = "Missed"
        reminder.status = "Failed"
        reminder.save(update_fields=["response_status", "status"])
        return reminder


def schedule_id_key(schedule, reminder_datetime):
    return f"{schedule.id}:{reminder_datetime.isoformat()}"
