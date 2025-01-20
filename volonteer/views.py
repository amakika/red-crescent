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

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
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
            # Debugging: Print incoming request data
            print("Incoming login request data:", request.data)
            
            username = request.data.get('username')
            password = request.data.get('password')

            # Validate input
            if not username or not password:
                return Response(
                    {'error': 'Both username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Debugging: Print before authentication
            print(f"Attempting to authenticate user: {username}")
            
            # Authenticate user
            user = authenticate(username=username, password=password)
            
            if user is None:
                # Debugging: Print authentication failure
                print(f"Authentication failed for user: {username}")
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Debugging: Print successful authentication
            print(f"User {username} authenticated successfully")
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Debugging: Print token generation
            print("Tokens generated successfully")
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })

        except Exception as e:
            # Enhanced error logging
            print(f"Error in LoginView: {str(e)}")
            logger.error(f"Error in LoginView: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


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
# Create your views here.
