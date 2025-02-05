from rest_framework import serializers
from .models import User, Task, Event, Leaderboard, Statistic, Achievement, TaskParticipation


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'criteria_hours', 'criteria_tasks']

    def validate_criteria_hours(self, value):
        if value < 0:
            raise serializers.ValidationError("Criteria hours must be a positive number.")
        return value

    def validate_criteria_tasks(self, value):
        if value < 0:
            raise serializers.ValidationError("Criteria tasks must be a positive number.")
        return value


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    achievements = AchievementSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'gender', 'role', 'phone_number', 'total_hours', 'xp_points',
            'profile_picture', 'profile_picture_url', 'achievements'
        ]
        extra_kwargs = {
            'profile_picture': {'write_only': True},
        }

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


class TaskParticipationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskParticipation
        fields = ['user', 'task', 'is_participated', 'joined_at']
        read_only_fields = ['joined_at']




from rest_framework import serializers
from .models import Task, TaskParticipation
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    assigned_volunteers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role='volunteer'),
        required=False
    )
    coordinator = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='coordinator'),
        required=False, allow_null=True
    )
    is_full = serializers.SerializerMethodField()
    is_participating = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_volunteers', 'coordinator',
            'status', 'due_date', 'hours_to_complete', 'location', 'is_public',
            'volunteer_limit', 'created_at', 'updated_at', 'is_full', 'is_participating'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_full(self, obj):
        return obj.is_full()
    
    def get_is_participating(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.is_participating(user)
        return False
    
    def validate_assigned_volunteers(self, volunteers):
        if len(volunteers) > self.instance.volunteer_limit:
            raise serializers.ValidationError("Assigned volunteers exceed the limit.")
        return volunteers


class EventSerializer(serializers.ModelSerializer):
    registered_volunteers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='volunteer'), many=True
    )
    coordinator = UserSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'coordinator', 'date', 'location', 'registered_volunteers', 'is_public'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value


class LeaderboardSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Leaderboard
        fields = ['id', 'user', 'rank', 'xp_points', 'total_hours']
        read_only_fields = ['rank', 'xp_points', 'total_hours']


class StatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistic
        fields = [
            'id', 'total_volunteers', 'total_hours', 'male_volunteers', 'female_volunteers',
            'other_gender_volunteers', 'updated_at'
        ]
        read_only_fields = ['updated_at']