from rest_framework.routers import DefaultRouter
from .views import UsersViewSet, LogoutView, RegisterView, DailyTaskTimeLeftView, DailyTaskViewSet, LeaderboardView, WeaklingsView, AchievemntViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'users', UsersViewSet, basename='user')
router.register(r'daily_tasks', DailyTaskViewSet, basename='dailytask')
router.register(r'achievements', AchievemntViewSet, basename='achievement')
# router.register(r'images', ImageViewSet, basename='image')
# router.register(r'reviews', ReviewViewSet, basename='review')
# router.register(r'baskets', BasketViewSet, basename='basket')
# router.register(r'orders', OrderViewSet, basename='order')
# router.register(r'promocodes', PromocodeViewSet, basename='promocode')

urlpatterns = [
    path('', include(router.urls)),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('register/', RegisterView.as_view(), name="register"),
    path('time-left/', DailyTaskTimeLeftView.as_view(), name='time-left'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('weaklings/', WeaklingsView.as_view(), name='weaklings'),
]