from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import User, Task, Event, Leaderboard, Statistic, Achievement
from django.db import transaction

# Custom AdminSite class to disable CSRF for admin views
class MyAdminSite(admin.AdminSite):
    @method_decorator(csrf_exempt)
    def admin_view(self, view, cacheable=False):
        return super().admin_view(view, cacheable)

# Create an instance of your custom admin site
admin_site = MyAdminSite(name="myadmin")

# Custom User Admin
@admin.register(User, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'profile_picture', 'achievements_list')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('achievements',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'gender', 'phone_number')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Volunteer Info', {'fields': ('role', 'total_hours', 'xp_points', 'profile_picture', 'achievements')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'phone_number', 'gender'),
        }),
    )

    def achievements_list(self, obj):
        return ", ".join([achievement.name for achievement in obj.achievements.all()])
    achievements_list.short_description = 'Achievements'

    def save_model(self, request, obj, form, change):
        # Disable admin logging for user creation
        with transaction.atomic():
            super().save_model(request, obj, form, change)

# Task Admin
@admin.register(Task, site=admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'coordinator', 'status', 'due_date', 'is_public')
    list_filter = ('status', 'is_public', 'due_date')
    search_fields = ('title', 'description')
    raw_id_fields = ('assigned_volunteers', 'coordinator')
    filter_horizontal = ('assigned_volunteers',)

# Event Admin
@admin.register(Event, site=admin_site)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'coordinator', 'date', 'location', 'is_public')
    list_filter = ('is_public', 'date')
    search_fields = ('title', 'description', 'location')
    raw_id_fields = ('registered_volunteers', 'coordinator')
    filter_horizontal = ('registered_volunteers',)

# Leaderboard Admin
@admin.register(Leaderboard, site=admin_site)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'xp_points', 'total_hours')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)

# Statistic Admin
@admin.register(Statistic, site=admin_site)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('total_volunteers', 'total_hours', 'male_volunteers', 'female_volunteers', 'other_gender_volunteers')
    list_filter = ('updated_at',)

# Achievement Admin
@admin.register(Achievement, site=admin_site)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'criteria_hours', 'criteria_tasks')
    search_fields = ('name', 'description')
    filter_horizontal = ('users',)