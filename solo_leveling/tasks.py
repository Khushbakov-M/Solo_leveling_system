from celery import shared_task
from datetime import timedelta
from .models import DailyTask, User, Achievement
from django.utils import timezone
import random


titles = [
    ("Monarch of the Month", "Awarded to the absolute ruler of the leaderboard, reigning supreme over all challengers."),
    ("S-Rank Hunter", "Given to the elite user who crushed every task and proved themselves as the strongest of the month."),
    ("Shadow Overlord", "For the one who moved in silence but dominated with unstoppable consistency."),
    ("Grandmaster of Growth", "Earned by the user who showed the most improvement, leveling up at an incredible rate."),
    ("Awakened Champion", "Given to the one who exceeded all expectations, breaking past their previous limits."),
    ("The Invincible", "Awarded to the top-ranked user who dominated without missing a single day."),
    ("Limit Breaker", "For the one who went beyond their limits, setting new records in training and perseverance."),
    ("Unstoppable", "This user showed no signs of slowing down, consistently ranking at the top."),
    ("Overlord of Growth", "For the one who gained the most experience and leveled up faster than anyone."),
    ("The Undefeated", "Awarded to the champion who remained at the top without being overtaken."),
    ("Master of Discipline", "Given to the user who completed every task without fail, proving extreme discipline."),
    ("God of Training", "This user treated every day like a challenge and trained harder than anyone else."),
    ("One Above All", "For the one who completely dominated this month, leaving no competition in sight."),
]


@shared_task
def create_daily_tasks():
    users = User.objects.all()

    # Get users who don't have a DailyTask for today
    users_without_tasks = [
        user for user in users 
        if not DailyTask.objects.filter(user=user, date=timezone.localdate()).exists()
    ]

    # Create DailyTask objects in bulk
    daily_tasks = [DailyTask(user=user) for user in users_without_tasks]

    if daily_tasks:
        DailyTask.objects.bulk_create(daily_tasks)  # Bulk create for efficiency
    
    return f"Daily tasks created for {len(daily_tasks)} users"


@shared_task
def punish_inactive_users():
    yesterday = timezone.localdate() - timedelta(days=1)
    incomplete_tasks = DailyTask.objects.filter(date=yesterday, is_completed=False)

    punished_users = set()
    for task in incomplete_tasks:
        user = task.user

        if user.streak > 0:
            user.streak = -1
        else:
            user.streak -= 1

        base_exp_loss= 70  # You should have this field in your User model
        extra_loss = 0
        if user.streak == -5:
            extra_loss = 200
        elif user.streak == -10:
            extra_loss = 300
        elif user.streak == -15:
            user.eliminate()
            break
        user.exp -= extra_loss + base_exp_loss
        user.this_month_exp -= extra_loss + base_exp_loss

        if user.exp >= 25000:
            user.rank = 'Jinwoo'
        elif user.exp >= 16000:
            user.rank = 'S'
        elif user.exp >= 8000:
            user.rank = 'A'
        elif user.exp >= 4000:
            user.rank = 'B'
        elif user.exp >= 1500:
            user.rank = 'C'
        elif user.exp >= 500:
            user.rank = 'D'
        else:
            user.rank = 'E'
        
        user.save()
        punished_users.add(user)

    return f"Punished {len(punished_users)} users for not completing yesterday's task."


@shared_task
def reset_exp_field():
    users = User.objects.all()
    top_1 = users.order_by('-this_month_exp')[0]
    if top_1.this_month_exp > 0:
        top_players = User.objects.filter(this_month_exp=top_1.this_month_exp)
    
    for top_player in top_players:
        title = random.choice(titles)
        Achievement.objects.create(
            user = top_player,
            title = title[0],
            description = title[1]
        )
    
    for user in users:
        user.this_month_exp = 0
        user.save()