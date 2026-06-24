"""
apps/accounts/models.py
Custom User model for GrowthPath with university student profile fields.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended User model capturing Nigerian university student profile data
    used by the recommendation engine for personalisation.
    """

    UNIVERSITY_YEAR_CHOICES = [
        (1, '100 Level'),
        (2, '200 Level'),
        (3, '300 Level'),
        (4, '400 Level'),
        (5, '500 Level'),
        (6, 'Postgraduate'),
    ]

    # Profile
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    university = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    year_of_study = models.PositiveSmallIntegerField(
        choices=UNIVERSITY_YEAR_CHOICES, null=True, blank=True
    )
    matric_number = models.CharField(max_length=20, blank=True)

    # Tracking
    daily_reminder = models.BooleanField(default=True)
    weekly_report = models.BooleanField(default=False)
    ai_personalisation = models.BooleanField(default=True)
    peak_hour_start = models.PositiveSmallIntegerField(default=7)   # 07:00
    peak_hour_end = models.PositiveSmallIntegerField(default=10)    # 10:00

    # Gamification
    streak_days = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_points = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.university})"

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        parts = self.display_name.split()
        return ''.join(p[0].upper() for p in parts[:2])


class Achievement(models.Model):
    """Badges and achievements unlocked by users."""

    CATEGORY_CHOICES = [
        ('streak', 'Streak'),
        ('goals', 'Goals'),
        ('skills', 'Skills'),
        ('productivity', 'Productivity'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='ti-award')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"
