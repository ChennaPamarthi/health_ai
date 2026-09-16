from datetime import date, timedelta

from django.db.models import Count

from health.models import Reminder


class AnalyticsService:
    """
    Generates medicine adherence analytics.
    """

    def get_today_summary(self, patient):
        today = date.today()

        reminders = Reminder.objects.filter(
            schedule__medicine__prescription__patient=patient,
            reminder_datetime__date=today,
        )

        total = reminders.count()
        completed = reminders.filter(status="Completed").count()
        missed = reminders.filter(status="Missed").count()
        pending = reminders.filter(
            status__in=[
                "Pending",
                "Sent",
            ]
        ).count()

        adherence = round((completed / total) * 100, 2) if total > 0 else 0

        return {
            "date": today,
            "total_reminders": total,
            "completed": completed,
            "missed": missed,
            "pending": pending,
            "adherence_percentage": adherence,
        }

    def get_week_summary(self, patient):
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        reminders = Reminder.objects.filter(
            schedule__medicine__prescription__patient=patient,
            reminder_datetime__date__range=[
                start_date,
                end_date,
            ],
        )

        total = reminders.count()
        completed = reminders.filter(status="Completed").count()
        missed = reminders.filter(status="Missed").count()
        adherence = round((completed / total) * 100, 2) if total > 0 else 0

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_reminders": total,
            "completed": completed,
            "missed": missed,
            "adherence_percentage": adherence,
        }

    def get_month_summary(self, patient):
        today = date.today()

        reminders = Reminder.objects.filter(
            schedule__medicine__prescription__patient=patient,
            reminder_datetime__date__year=today.year,
            reminder_datetime__date__month=today.month,
        )

        total = reminders.count()
        completed = reminders.filter(status="Completed").count()
        missed = reminders.filter(status="Missed").count()
        adherence = round((completed / total) * 100, 2) if total > 0 else 0

        return {
            "month": today.month,
            "year": today.year,
            "total_reminders": total,
            "completed": completed,
            "missed": missed,
            "adherence_percentage": adherence,
        }

    def get_most_missed_medicines(self, patient, limit=5):
        medicines = (
            Reminder.objects.filter(
                schedule__medicine__prescription__patient=patient,
                status="Missed",
            )
            .values("schedule__medicine__medicine_name")
            .annotate(missed_count=Count("id"))
            .order_by("-missed_count")[:limit]
        )

        return list(medicines)

    def get_dashboard(self, patient):
        return {
            "today": self.get_today_summary(patient),
            "week": self.get_week_summary(patient),
            "month": self.get_month_summary(patient),
            "most_missed": self.get_most_missed_medicines(patient),
        }
