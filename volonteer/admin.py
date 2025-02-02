from django.contrib import admin
from .models import Achievement, User, Task, TaskParticipation, Event, Leaderboard, Statistic


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'criteria_hours', 'criteria_tasks')
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'gender', 'phone_number', 'total_hours', 'xp_points')
    search_fields = ('username', 'email', 'role')
    list_filter = ('role', 'gender')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'coordinator', 'due_date', 'hours_to_complete', 'volunteer_limit', 'is_public')
    search_fields = ('title', 'status', 'coordinator__username')
    list_filter = ('status', 'is_public', 'due_date')


@admin.register(TaskParticipation)
class TaskParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_participated', 'joined_at')
    search_fields = ('user__username', 'task__title')
    list_filter = ('is_participated', 'joined_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'coordinator', 'date', 'location', 'is_public')
    search_fields = ('title', 'coordinator__username', 'location')
    list_filter = ('date', 'is_public')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'xp_points', 'total_hours')
    search_fields = ('user__username', 'rank')
    list_filter = ('rank',)


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('total_volunteers', 'total_hours', 'male_volunteers', 'female_volunteers', 'other_gender_volunteers', 'updated_at')
    search_fields = ('total_volunteers',)
    list_filter = ('updated_at',)