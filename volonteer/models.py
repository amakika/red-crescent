from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework_simplejwt.tokens import RefreshToken
from cloudinary.models import CloudinaryField
import requests
from io import BytesIO
from PIL import Image
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    criteria_hours = models.PositiveIntegerField(default=0, blank=True, null=True)
    criteria_tasks = models.PositiveIntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name



class User(AbstractUser):
    ROLE_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('coordinator', 'Coordinator'),
        ('admin', 'Admin'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, db_index=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, null=True, blank=True, db_index=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    total_hours = models.FloatField(default=0.0)
    xp_points = models.IntegerField(default=0)
    profile_picture = CloudinaryField('image', null=True, blank=True)
    achievements = models.ManyToManyField('Achievement', blank=True, related_name='users')

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        # Remove image validation logic
        super().save(*args, **kwargs)

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    photo = CloudinaryField('image', null=True, blank=True)
    assigned_volunteers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TaskParticipation',
        related_name='tasks',
        blank=True,
        limit_choices_to={'role': 'volunteer'}
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coordinator_tasks',
        limit_choices_to={'role': 'coordinator'}
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', db_index=True)
    due_date = models.DateTimeField()
    hours_to_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=False, db_index=True)
    volunteer_limit = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_full(self):
        return self.assigned_volunteers.count() >= self.volunteer_limit

    def is_participating(self, user):
        return TaskParticipation.objects.filter(user=user, task=self).exists()

    def add_participant(self, user):
        if self.is_full():
            raise ValidationError("This task has reached its volunteer limit.")
        if user.role != 'volunteer':
            raise ValidationError("Only volunteers can participate in tasks.")
        TaskParticipation.objects.get_or_create(user=user, task=self, is_participated=True)

    def remove_participant(self, user):
        TaskParticipation.objects.filter(user=user, task=self).delete()


class TaskParticipation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_participated = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')

    def __str__(self):
        return f"{self.user.username} - {self.task.title} (Participated: {self.is_participated})"


@receiver(post_save, sender=User)
def create_jwt_token(sender, instance, created, **kwargs):
    if created:
        RefreshToken.for_user(instance)


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    coordinator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='coordinator_events', limit_choices_to={'role': 'coordinator'}
    )
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    registered_volunteers = models.ManyToManyField(User, related_name='registered_events', blank=True)
    is_public = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title


class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard')
    rank = models.IntegerField(default=0)
    xp_points = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username} - Rank: {self.rank}"


class Statistic(models.Model):
    total_volunteers = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    male_volunteers = models.IntegerField(default=0)
    female_volunteers = models.IntegerField(default=0)
    other_gender_volunteers = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Global Statistics"
