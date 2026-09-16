from django.core.management.base import BaseCommand

from health.tasks.reminder_tasks import ReminderTask


class Command(BaseCommand):
    help = "Run one reminder cycle to send due reminders and mark missed logs."

    def handle(self, *args, **options):
        result = ReminderTask().run()
        self.stdout.write(self.style.SUCCESS(str(result)))
