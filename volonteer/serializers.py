from rest_framework import serializers
from .models import User, Task, Event, Leaderboard, Statistic, Achievement


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'profile_picture': {'write_only': True},
            'profile_picture_width': {'read_only': True},
            'profile_picture_height': {'read_only': True},
        }

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

    def get_achievements(self, obj):
        return AchievementSerializer(obj.achievements.all(), many=True).data


class CoordinatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number']  # Include additional fields if needed


class TaskSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)
    coordinator = CoordinatorSerializer(read_only=True)
    assigned_volunteers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='volunteer'), many=True
    )

    class Meta:
        model = Task
        fields = '__all__'

    def validate_criteria_hours(self, value):
        if value < 0:
            raise serializers.ValidationError("Criteria hours must be a positive number.")
        return value


class EventSerializer(serializers.ModelSerializer):
    registered_volunteers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='volunteer'), many=True
    )
    coordinator = CoordinatorSerializer(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'


class LeaderboardSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Leaderboard
        fields = '__all__'


class StatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistic
        fields = '__all__'


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