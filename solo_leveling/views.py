from django.utils import timezone
from rest_framework.decorators import action
from .models import User, DailyTask
from  .serializers import UserSerializer, LogoutSerializer, DailyTaskSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, time
from django.utils import timezone

# Create your views here.
class DailyTaskTimeLeftView(APIView):
    def get(self, request):
        now = timezone.localtime()  # Get the current time in the local timezone
        end_of_day = datetime.combine(now.date(), time(23, 59, 59))  # Naive datetime

        # Ensure end_of_day is in the same timezone as now
        end_of_day = timezone.make_aware(end_of_day, timezone.get_current_timezone())

        time_left = (end_of_day - now).total_seconds()
        return Response({"time_left": max(0, int(time_left))})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token required"}, status=400)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Successfully logged out"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class RegisterView(APIView):
    serializer_class = UserSerializer

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get', 'put', 'delete'])
    def profile(self, request):
        user = request.user
        
        if request.method == 'GET':
            """Return user profile"""
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == 'PUT':
            """Update user profile"""
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            """Delete user profile"""
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path="reset-profile")
    def reset_profile(self, request):
        user = request.user
        user.exp = 0
        user.rank = 'E'
        user.streak = 0
        user.last_task_date = None
        user.last_emergency_task_date = None
        user.date_joined = timezone.now()
        user.last_login = timezone.now()
        user.save()
        return Response({"message": "Profile reset successfully"})


class DailyTaskViewSet(viewsets.ModelViewSet):
    queryset = DailyTask.objects.all()
    serializer_class = DailyTaskSerializer
    
    @action(detail=False, methods=['get', 'put'])
    def mine(self, request):
        user = request.user
        today = timezone.now().date()
        
        try:
            daily_task = DailyTask.objects.get(user=user, date=today)
        except DailyTask.DoesNotExist:
            daily_task = None

        if request.method == "GET":
            if daily_task:
                serializer = self.get_serializer(daily_task)
                return Response(serializer.data)
            return Response({"error": "No daily task found for today."}, status=status.HTTP_404_NOT_FOUND)

        elif request.method == "PUT":
            if not daily_task:
                return Response({"error": "You cannot update a non-existent daily task."}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(daily_task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)