from django.contrib import admin
from .models import User, Achievement, Task, TaskParticipation, Event, Leaderboard, Statistic

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'gender', 'total_hours', 'xp_points')
    search_fields = ('username', 'email', 'role')
    list_filter = ('role', 'gender')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'criteria_hours', 'criteria_tasks')
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'coordinator', 'due_date', 'volunteer_limit')
    search_fields = ('title', 'status')
    list_filter = ('status', 'is_public')

@admin.register(TaskParticipation)
class TaskParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_participating', 'joined_at')
    search_fields = ('user__username', 'task__title')
    list_filter = ('is_participating',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'coordinator', 'is_public')
    search_fields = ('title', 'location')
    list_filter = ('is_public',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'xp_points', 'total_hours')
    search_fields = ('user__username',)

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('total_volunteers', 'total_hours', 'male_volunteers', 'female_volunteers', 'other_gender_volunteers', 'updated_at')
