from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # This ensures the password is hashed
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    exp = models.IntegerField(default=0)
    this_month_exp = models.IntegerField(default=0)
    rank = models.CharField(max_length=10, choices=[('E', 'E'),('D', 'D'),('C', 'C'),('B', 'B'),('A', 'A'),('S', 'S'),('Jinwoo','Jinwoo')], default="E")
    streak = models.IntegerField(default=0)
    last_task_date = models.DateField(null=True, blank=True)
    last_emergency_task_date = models.DateField(null=True, blank=True)
    eliminated_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.pk:
            original_password = User.objects.get(pk=self.pk).password
            if self.password != original_password and not check_password(self.password, original_password):
                self.password = make_password(self.password)
        else:
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    
    def eliminate(self):
        self.exp = 0
        self.rank = 'E'
        self.this_month_exp = 0
        self.streak = 0
        self.last_task_date = None
        self.last_emergency_task_date = None
        self.eliminated_at = timezone.now()  # Add this if you want to track elimination time
        self.save()

    def create_initial_task_if_needed(self):
        now = timezone.localtime()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        time_remaining = (end_of_day - now).total_seconds() / 3600  # Convert to hours

        if time_remaining >= 4:
            DailyTask.objects.create(user=self)


class DailyTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    pushups = models.IntegerField(default=50)
    situps = models.IntegerField(default=50)
    squats = models.IntegerField(default=50)
    running_km = models.FloatField(default=5.0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'date')

    def save(self, *args, **kwargs):
        if self.pk and DailyTask.objects.filter(pk=self.pk).exists():
            previous_task = DailyTask.objects.get(pk=self.pk)

            # Prevent marking a completed task as incomplete
            if previous_task.is_completed and not self.is_completed:
                raise ValueError("You cannot mark a completed task as incomplete.")

            # Check if task is being marked as completed for the first time
            if not previous_task.is_completed and self.is_completed:
                user = self.user

                # Streak handling
                if user.streak < 0:
                    user.streak = 1  # Reset skipping streak
                else:
                    user.streak += 1  # Increase streak

                # Calculate EXP
                base_exp = 50  # Base EXP for completing a task
                exp_bonus = 0  

                if user.streak % 10 == 0:
                    exp_bonus += 300  # Bonus for 10-day streak
                if user.streak % 30 == 0:
                    exp_bonus += 1000  # Bonus for 30-day streak

                user.exp += base_exp + exp_bonus  # Add EXP
                user.this_month_exp += base_exp + exp_bonus

                # Rank calculation (check from highest to lowest)
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

                # Save user changes
                user.last_task_date = self.date
                user.save()

        # Call the original save method
        super().save(*args, **kwargs)


class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=800)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"
    

class Notification(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.title}"


# class EmergencyTask(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     description = models.TextField()
#     difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
#     exp_reward = models.IntegerField()
#     exp_penalty = models.IntegerField()
#     deadline = models.DateTimeField()
#     proof_image = models.ImageField(upload_to="emergency_tasks/", null=True, blank=True)
#     is_completed = models.BooleanField(default=False)


# class Punishment(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     task_type = models.CharField(max_length=20, choices=TASK_TYPES)
#     exp_lost = models.IntegerField()
#     reason = models.TextField()
#     date = models.DateField(auto_now_add=True)


# class Reward(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     rank_required = models.CharField(max_length=10, choices=RANK_CHOICES)
#     reward_type = models.CharField(max_length=50, choices=REWARD_TYPES)
#     is_claimed = models.BooleanField(default=False)


# class AIAnalysis(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     analysis_type = models.CharField(max_length=20, choices=ANALYSIS_CHOICES)
#     result_data = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
