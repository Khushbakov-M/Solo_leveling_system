from rest_framework import serializers
from .models import User, DailyTask

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(max_length=200)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "url",
            "email",
            "exp",
            "rank",
            "streak",
            "last_task_date",
            "last_emergency_task_date",
            "first_name",
            "last_name",
            "password",
            "date_joined",
            "last_login"
        ]
        read_only_fields = [
            'exp',
            'rank',
            'streak',
            'last_task_date',
            'last_emergency_task_date',
            'date_joined',
            'last_login'
        ]


class DailyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyTask
        fields = [
            "id",
            "url",
            "user",
            "date",
            "pushups",
            "situps",
            "squats",
            "running_km",
            "is_completed",
        ]
        read_only_fields = [
            "date",
            "pushups",
            "situps",
            "squats",
            "running_km"
        ]

    def validate_is_completed(self, value):
        if self.instance and self.instance.is_completed and not value:
            raise serializers.ValidationError("You cannot mark a completed task as incomplete.")
        return value