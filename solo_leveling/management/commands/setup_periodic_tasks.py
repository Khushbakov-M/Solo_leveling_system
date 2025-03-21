from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = "Sets up the periodic task to create daily tasks"

    def handle(self, *args, **kwargs):
        # Create or get a schedule for every 24 hours
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS
        )

        # Create the periodic task if it doesn't exist
        task, created = PeriodicTask.objects.get_or_create(
            name="Create Daily Tasks at Midnight",
            defaults={
                "interval": schedule,
                "task": "your_app.tasks.create_daily_tasks",
                "args": json.dumps([]),
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Periodic task created successfully."))
        else:
            self.stdout.write(self.style.WARNING("Periodic task already exists."))
