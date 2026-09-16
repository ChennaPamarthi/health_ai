from health.tasks.reminder_tasks import ReminderTask


class ReminderScheduler:
    """
    Thin scheduling facade for running one reminder cycle.
    """

    def __init__(self):
        self.task = ReminderTask()

    def run_once(self):
        return self.task.run()

