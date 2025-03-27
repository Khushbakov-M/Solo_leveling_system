from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = "Creates periodic tasks for generating daily tasks and punishing inactive users at 00:00"

    def handle(self, *args, **kwargs):
        # Schedule for both tasks at 00:00 (midnight Tashkent time)
        midnight_schedule, _ = CrontabSchedule.objects.update_or_create(
            minute=0, hour=0, day_of_week="*", day_of_month="*", month_of_year="*", timezone="Asia/Tashkent"
        )

        resetting_schedule, _ = CrontabSchedule.objects.update_or_create(
            minute=5, hour=0, day_of_week="*", day_of_month="1", month_of_year="*", timezone="Asia/Tashkent"
        )

        # Create or update the "Create Daily Tasks" task
        PeriodicTask.objects.update_or_create(
            name="Create Daily Tasks",
            defaults={
                "crontab": midnight_schedule,
                "task": "solo_leveling.tasks.create_daily_tasks",
                "args": json.dumps([]),
            },
        )

        # Create or update the "Punish Inactive Users" task
        PeriodicTask.objects.update_or_create(
            name="Punish Inactive Users",
            defaults={
                "crontab": midnight_schedule,
                "task": "solo_leveling.tasks.punish_inactive_users",
                "args": json.dumps([]),
            },
        )

        PeriodicTask.objects.update_or_create(
            name="Reset Exp for month",
            defaults={
                "crontab": resetting_schedule,
                "task": "solo_leveling.tasks.reset_exp_field",
                "args": json.dumps([]),
            },
        )

        self.stdout.write(self.style.SUCCESS("Periodic tasks scheduled successfully at 00:00!"))
