from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, Achievement, Task, TaskParticipation, Event, Leaderboard, Statistic


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'total_hours', 'xp_points', 'profile_picture_preview')
    list_filter = ('role', 'gender', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-xp_points',)
    readonly_fields = ('profile_picture_preview',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'gender', 'phone_number')}),
        (_('Role & Status'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Achievements & XP'), {'fields': ('xp_points', 'total_hours', 'achievements')}),
        (_('Profile Picture'), {'fields': ('profile_picture', 'profile_picture_preview')}),
        (_('Permissions'), {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active'),
        }),
    )

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%"/>', obj.profile_picture.url)
        return "-"
    
    profile_picture_preview.short_description = "Profile Picture"


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'criteria_hours', 'criteria_tasks')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'due_date', 'volunteer_limit', 'is_full')
    list_filter = ('status', 'is_public')
    search_fields = ('title', 'coordinator__username')
    ordering = ('-due_date',)

    def is_full(self, obj):
        return obj.is_full()
    is_full.boolean = True


@admin.register(TaskParticipation)
class TaskParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_participating', 'joined_at')
    list_filter = ('is_participating',)
    search_fields = ('user__username', 'task__title')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'is_public')
    list_filter = ('is_public',)
    search_fields = ('title', 'coordinator__username')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'xp_points', 'total_hours')
    ordering = ('rank',)


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('total_volunteers', 'total_hours', 'male_volunteers', 'female_volunteers', 'other_gender_volunteers', 'updated_at')
    readonly_fields = ('updated_at',)
