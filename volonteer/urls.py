from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, UserViewSet, TaskViewSet,
    EventViewSet, LeaderboardViewSet, StatisticViewSet,MeView,CheckAchievementsView,
    TotalHoursStatsView,
    CompletedTasksStatsView,
    GenderStatsView,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tasks', TaskViewSet, basename='task')
router.register('events', EventViewSet, basename='event')
router.register('leaderboard', LeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('statistics/', StatisticViewSet.as_view(), name='statistics'),
    path('', include(router.urls)),
    path('me/', MeView.as_view(), name='me'),
    path('check-achievements/', CheckAchievementsView.as_view(), name='check-achievements'),
    path('api/stats/total-hours/', TotalHoursStatsView.as_view(), name='total-hours-stats'),
    path('api/stats/completed-tasks/', CompletedTasksStatsView.as_view(), name='completed-tasks-stats'),
    path('api/stats/gender-stats/', GenderStatsView.as_view(), name='gender-stats'),
]