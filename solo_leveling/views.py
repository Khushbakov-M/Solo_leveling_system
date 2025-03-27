from django.utils import timezone
from rest_framework.decorators import action
from .models import User, DailyTask, Achievement
from  .serializers import UserSerializer, LogoutSerializer, DailyTaskSerializer, AchievementSerializer
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .permissions import IsNotAuthenticated

# Create your views here.
class DailyTaskTimeLeftView(APIView):
    def get(self, request):
        now = timezone.localtime()  # Get the current local time
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)  # Set to end of day

        time_left = (end_of_day - now).total_seconds()
        return Response({"time_left": max(0, int(time_left))})


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=200)
        except TokenError:  # More specific error handling
            return Response({"error": "Invalid or already blacklisted token"}, status=400)


class RegisterView(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsNotAuthenticated]

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()  # Save the user first
            user.create_initial_task_if_needed()  # Create daily task if enough time left

            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        users = User.objects.all().order_by('-this_month_exp')[:10]
        leaderboard = []
        for user in users:
            leaderboard.append({'user' : f'{user.email}({user.first_name} {user.last_name})', 'exp' : user.this_month_exp})
        return Response(leaderboard)


class WeaklingsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        users = User.objects.all().order_by('this_month_exp')[:10]
        weaklings = []
        for user in users:
            weaklings.append({'user' : f'{user.email}({user.first_name} {user.last_name})', 'exp' : user.this_month_exp})
        return Response(weaklings)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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
        user.eliminate()
        return Response({"message": "Profile reset successfully"})


class DailyTaskViewSet(viewsets.ModelViewSet):
    queryset = DailyTask.objects.all()
    serializer_class = DailyTaskSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put'])
    def mine(self, request):
        user = request.user
        today = timezone.localtime().date()
        
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
            
            serializer = self.get_serializer(daily_task, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def history(self, request):
        user = request.user
        daily_tasks = DailyTask.objects.filter(user=user).order_by('date')
        if daily_tasks.exists():
            serializer = self.get_serializer(daily_tasks, many=True)
            return Response(serializer.data)
        return Response({"error": "No daily task found for history"})


class AchievemntViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my(self, request):
        achievements = Achievement.objects.filter(user=request.user)
        if achievements.exists():
            serializer = self.get_serializer(achievements, many=True)
            return Response(serializer.data)
        return Response({"error":"No achievements found for this user"})
            
    
    @action(detail=False, methods=['get'], url_path='my/last')
    def my_last_achievement(self, reqeust):
        last = Achievement.objects.filter(user=reqeust.user).order_by('-created_at').first()
        if last:
            serializer = self.get_serializer(last)
            return Response(serializer.data)
        return Response({"error":"No achivement found"})