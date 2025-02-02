from django.db import models
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework_simplejwt.tokens import RefreshToken

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from cloudinary.models import CloudinaryField
from cloudinary.models import CloudinaryField

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image
 
class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    criteria_hours = models.PositiveIntegerField(default=0, blank=True, null=True)
    criteria_tasks = models.PositiveIntegerField(default=0, blank=True, null=True)
    users = models.ManyToManyField(
        'User', 
        blank=True, 
        related_name='achievement_users'  # Unique related_name
    )

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

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    total_hours = models.FloatField(default=0.0)
    xp_points = models.IntegerField(default=0)
    profile_picture = CloudinaryField('image', null=True, blank=True)
    profile_picture_width = models.PositiveIntegerField(null=True, blank=True)
    profile_picture_height = models.PositiveIntegerField(null=True, blank=True)
    achievements = models.ManyToManyField(
        'Achievement', 
        blank=True, 
        related_name='user_achievements'  # Unique related_name
    )
    

    def save(self, *args, **kwargs):
        # Only process image if it's being updated
        if self.profile_picture and hasattr(self.profile_picture, 'file'):
            try:
                from PIL import Image
                import io
                
                # Open the image file
                img = Image.open(self.profile_picture)
                
                # Get dimensions
                width, height = img.size
                
                # Save dimensions to model fields
                self.profile_picture_width = width
                self.profile_picture_height = height
                
                # Save the image to a BytesIO buffer
                buffer = io.BytesIO()
                img.save(buffer, format=img.format)
                self.profile_picture.file = buffer
                
            except Exception as e:
                # Handle image processing errors gracefully
                print(f"Error processing image: {e}")
                self.profile_picture_width = None
                self.profile_picture_height = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def clean(self):
        super().clean()
        if self.profile_picture:
            try:
                img = Image.open(self.profile_picture)
                img.verify()  # Verify that it is, in fact, an image
            except Exception as e:
                raise ValidationError({'profile_picture': 'Invalid image file'})






class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=255, help_text="Enter the title of the task.")
    description = models.TextField(help_text="Provide a detailed description of the task.")
    photo = CloudinaryField('image', null=True, blank=True, help_text="Upload a photo related to the task.")
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
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', help_text="Select the current status of the task.")
    due_date = models.DateTimeField(help_text="Set the due date for the task.")
    hours_to_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Estimate the number of hours required to complete the task.")
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Specify the location where the task will be performed.")
    is_public = models.BooleanField(default=False, help_text="Check this box to make the task visible to all users.")
    volunteer_limit = models.PositiveIntegerField(default=0, help_text="Maximum number of volunteers allowed for this task.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_full(self):
        """Check if the task has reached its volunteer limit."""
        return self.assigned_volunteers.count() >= self.volunteer_limit

    def add_participant(self, user):
        """
        Add a volunteer to the task and set their participation status.
        Raises a ValidationError if the task is full or the user is not a volunteer.
        """
        if self.is_full():
            raise ValidationError("This task has reached its volunteer limit.")

        if not user.role == 'volunteer':
            raise ValidationError("Only volunteers can participate in tasks.")

        # Add the volunteer to the task and set their participation status
        TaskParticipation.objects.create(user=user, task=self, is_participating=True)

    def remove_participant(self, user):
        """
        Remove a volunteer from the task.
        """
        participation = TaskParticipation.objects.filter(user=user, task=self).first()
        if participation:
            participation.delete()

    def save(self, *args, **kwargs):
        """Ensure the number of volunteers does not exceed the limit when saving the task."""
        if self.assigned_volunteers.count() > self.volunteer_limit:
            raise ValidationError("The number of volunteers exceeds the limit.")
        super().save(*args, **kwargs)


class TaskParticipation(models.Model):
    """
    Through model for the Many-to-Many relationship between Task and User.
    Tracks whether a volunteer is actively participating in a task.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_participating = models.BooleanField(default=False, help_text="Whether the volunteer is actively participating in the task.")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')  # Ensure a volunteer can only join a task once

    def __str__(self):
        return f"{self.user.username} - {self.task.title} (Participating: {self.is_participating})"

@receiver(post_save, sender=User)
def create_jwt_token(sender, instance, created, **kwargs):
    if created:
        # Создаем токены для нового пользователя
        refresh = RefreshToken.for_user(instance)
        # Можно сохранить или отправить токены пользователю
        print(f"Access Token: {refresh.access_token}")
        print(f"Refresh Token: {refresh}")




class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    coordinator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='coordinator_events', limit_choices_to={'role': 'coordinator'}
    )
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    registered_volunteers = models.ManyToManyField(User, related_name='registered_events', blank=True)
    is_public = models.BooleanField(default=False)  # New field for visibility

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



# Create your models here.
