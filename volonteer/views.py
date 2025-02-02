from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from .models import User, Task, Event, Leaderboard, Achievement, TaskParticipation
from .serializers import (
    UserSerializer,
    TaskSerializer,
    EventSerializer,
    LeaderboardSerializer,
    AchievementSerializer,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
import logging

logger = logging.getLogger(__name__)


# Pagination Classes
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# Authentication and User Views
class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserSerializer(user).data
        return Response(user_data, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data if hasattr(user, 'id') else {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data
        })


# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['total_hours']
    ordering = ['-total_hours']

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering')
        if ordering == 'total_hours':
            return queryset.order_by('total_hours')
        elif ordering == '-total_hours':
            return queryset.order_by('-total_hours')
        return queryset


# Task ViewSet
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter tasks based on user role (e.g., volunteers see only open tasks).
        """
        user = self.request.user
        if user.role == 'volunteer':
            return Task.objects.filter(is_active=True)
        return Task.objects.all()

    @action(detail=True, methods=['get'])
    def is_participating(self, request, pk=None):
        """
        Checks if the authenticated user is participating in the task.
        """
        task = get_object_or_404(Task, pk=pk)
        user = request.user
        is_participating = TaskParticipation.objects.filter(user=user, task=task).exists()

        return Response({'is_participating': is_participating}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def participate(self, request, pk=None):
        """
        Allows a user to participate in a task. Returns boolean status.
        """
        task = get_object_or_404(Task, pk=pk)
        user = request.user

        if user.role != 'volunteer':
            return Response(
                {'error': 'Only volunteers can participate.', 'is_participating': False},
                status=status.HTTP_403_FORBIDDEN
            )

        if task.is_full():
            return Response(
                {'error': 'Task is full.', 'is_participating': False},
                status=status.HTTP_400_BAD_REQUEST
            )

        participation, created = TaskParticipation.objects.get_or_create(user=user, task=task)

        if not created:
            return Response(
                {'error': 'Already participating.', 'is_participating': True},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': 'Participation successful.', 'is_participating': True},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Allows a user to leave a task.
        """
        task = get_object_or_404(Task, pk=pk)
        user = request.user

        participation = TaskParticipation.objects.filter(user=user, task=task)
        if participation.exists():
            participation.delete()
            return Response(
                {'message': 'Successfully left the task.', 'is_participating': False},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': 'You are not participating in this task.', 'is_participating': False},
            status=status.HTTP_400_BAD_REQUEST
        )

# Event ViewSet
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['coordinator', 'admin']:
            return Response(
                {'error': 'Only coordinators or admins can create events.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(coordinator=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'volunteer':
            return Event.objects.filter(is_public=True) | Event.objects.filter(registered_volunteers=user)
        elif user.role == 'coordinator':
            return Event.objects.filter(coordinator=user)
        return Event.objects.all()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        if user in event.registered_volunteers.all():
            return Response(
                {'error': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.registered_volunteers.add(user)
        return Response(
            {'success': f'You have registered for the event "{event.title}".'},
            status=status.HTTP_200_OK
        )


# Leaderboard ViewSet
class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all().order_by('-xp_points')
    serializer_class = LeaderboardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# Statistics and Analytics Views
class StatisticViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['coordinator', 'admin']:
            return Response(
                {'error': 'Only coordinators or admins can view statistics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        stats = {
            'total_tasks': Task.objects.count(),
            'completed_tasks': Task.objects.filter(status='completed').count(),
            'total_events': Event.objects.count(),
            'total_volunteers': User.objects.filter(role='volunteer').count(),
            'total_coordinators': User.objects.filter(role='coordinator').count(),
        }
        return Response(stats, status=status.HTTP_200_OK)


class CheckAchievementsView(APIView):
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        achievements = Achievement.objects.all()
        unlocked = []

        for achievement in achievements:
            if (user.total_hours >= achievement.criteria_hours and
                user.completed_tasks >= achievement.criteria_tasks and
                achievement not in user.achievements.all()):
                user.achievements.add(achievement)
                unlocked.append(achievement)

        serializer = AchievementSerializer(unlocked, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TotalHoursStatsView(APIView):
    def get(self, request):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        stats = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).extra(
            {'month': "to_char(date_joined, 'YYYY-MM')"}
        ).values('month').annotate(
            total_hours=Sum('total_hours')
        ).order_by('month')

        return Response(stats)


class CompletedTasksStatsView(APIView):
    def get(self, request):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        stats = Task.objects.filter(
            created_at__range=[start_date, end_date],
            status='completed'
        ).extra(
            {'month': "to_char(created_at, 'YYYY-MM')"}
        ).values('month').annotate(
            completed_tasks=Count('id')
        ).order_by('month')

        return Response(stats)


class GenderStatsView(APIView):
    def get(self, request):
        stats = User.objects.values('gender').annotate(
            total_hours=Sum('total_hours'),
            completed_tasks=Sum('completed_tasks')
        )

        result = {
            'male': {'total_hours': 0, 'completed_tasks': 0},
            'female': {'total_hours': 0, 'completed_tasks': 0},
        }

        for item in stats:
            if item['gender'] == 'male':
                result['male'] = {
                    'total_hours': item['total_hours'],
                    'completed_tasks': item['completed_tasks']
                }
            elif item['gender'] == 'female':
                result['female'] = {
                    'total_hours': item['total_hours'],
                    'completed_tasks': item['completed_tasks']
                }

        return Response(result)