from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from .models import User, Task, Event, Leaderboard, Achievement
from .serializers import (
    UserSerializer,
    TaskSerializer,
    EventSerializer,
    LeaderboardSerializer,
    AchievementSerializer,
)
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import UserSerializer
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from rest_framework.pagination import PageNumberPagination
import logging
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the current authenticated user
        user = request.user
        
        # Serialize the user data
        user_data = UserSerializer(user).data

        # Return the user data
        return Response(user_data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
# Login Endpoint for JWT Tokens
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = authenticate(username=username, password=password)

            if user is None:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)
            
            # Use a simplified user data response if serializer fails
            try:
                user_data = UserSerializer(user).data
            except Exception as e:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data
            })

        except Exception as e:
            logger.error(f"Error in LoginView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['totalhours']
    ordering = ['-totalhours']

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', None)
        
        if ordering == 'totalhours':
            return queryset.order_by('totalhours')
        elif ordering == '-totalhours':
            return queryset.order_by('-totalhours')
            
        return queryset


# Task ViewSet
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['coordinator', 'admin']:
            return Response({'error': 'Only coordinators or admins can create tasks.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(coordinator=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'volunteer':
            return self.queryset.filter(is_public=True) | self.queryset.filter(assigned_volunteers=user)
        elif user.role == 'coordinator':
            return self.queryset.filter(coordinator=user)
        return self.queryset.filter(is_public=True)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def participate(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        user = request.user

        if task.status != 'pending':
            return Response({'error': 'Only pending tasks can be joined.'}, status=status.HTTP_400_BAD_REQUEST)

        if user in task.assigned_volunteers.all():
            return Response({'error': 'You are already assigned to this task.'}, status=status.HTTP_400_BAD_REQUEST)

        task.assigned_volunteers.add(user)
        return Response({'success': f'You have joined the task "{task.title}".'}, status=status.HTTP_200_OK)


# Event ViewSet
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['coordinator', 'admin']:
            return Response({"error": "Only coordinators or admins can create events."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(coordinator=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'volunteer':
            return self.queryset.filter(is_public=True) | self.queryset.filter(registered_volunteers=user)
        elif user.role == 'coordinator':
            return self.queryset.filter(coordinator=user)
        return self.queryset.filter(is_public=True)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        if user in event.registered_volunteers.all():
            return Response({'error': 'You are already registered for this event.'}, status=status.HTTP_400_BAD_REQUEST)

        event.registered_volunteers.add(user)
        return Response({'success': f'You have registered for the event "{event.title}".'}, status=status.HTTP_200_OK)


# Leaderboard ViewSet
class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all().order_by('-xp_points')
    serializer_class = LeaderboardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# Statistics Endpoint
class StatisticViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['coordinator', 'admin']:
            return Response({"error": "Only coordinators or admins can view statistics."}, status=status.HTTP_403_FORBIDDEN)

        stats = {
            "total_tasks": Task.objects.count(),
            "completed_tasks": Task.objects.filter(status='completed').count(),
            "total_events": Event.objects.count(),
            "total_volunteers": User.objects.filter(role='volunteer').count(),
            "total_coordinators": User.objects.filter(role='coordinator').count(),
        }
        return Response(stats, status=status.HTTP_200_OK)

class CheckAchievementsView(APIView):
    def post(self, request, user_id):
        user = User.objects.get(id=user_id)
        achievements = Achievement.objects.all()
        unlocked = []

        for achievement in achievements:
            if (user.total_hours >= achievement.criteria_hours and
                user.completed_tasks >= achievement.criteria_tasks and
                achievement not in user.achievements.all()):
                user.achievements.add(achievement)  # Add the achievement to the user
                unlocked.append(achievement)

        serializer = AchievementSerializer(unlocked, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TotalHoursStatsView(APIView):
    def get(self, request):
        # Получаем данные за последние 12 месяцев
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        # Группируем по месяцам и суммируем total_hours
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
        # Получаем данные за последние 12 месяцев
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        # Группируем по месяцам и считаем completed tasks
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
        # Группируем по полу и считаем total_hours и completed_tasks
        stats = User.objects.values('gender').annotate(
            total_hours=Sum('total_hours'),
            completed_tasks=Sum('completed_tasks')
        )

        # Преобразуем в удобный формат
        result = {
            'male': {'total_hours': 0, 'completed_tasks': 0},
            'female': {'total_hours': 0, 'completed_tasks': 0},
        }

        for item in stats:
            if item['gender'] == 'male':
                result['male']['total_hours'] = item['total_hours']
                result['male']['completed_tasks'] = item['completed_tasks']
            elif item['gender'] == 'female':
                result['female']['total_hours'] = item['total_hours']
                result['female']['completed_tasks'] = item['completed_tasks']

        return Response(result)

# Create your views here.
