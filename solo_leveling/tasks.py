from celery import shared_task
from datetime import date
from .models import DailyTask, User

@shared_task
def create_daily_tasks():
    users = User.objects.all()
    
    for user in users:
        # Check if a DailyTask already exists for today
        if not DailyTask.objects.filter(user=user, date=date.today()).exists():
            DailyTask.objects.create(user=user)
    
    return f"Daily tasks created for {users.count()} users"