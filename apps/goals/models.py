"""
apps/goals/models.py
Goal and milestone tracking with metrics, categories, and progress monitoring.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Goal(models.Model):

    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('technical', 'Technical'),
        ('career', 'Career'),
        ('personal', 'Personal'),
        ('health', 'Health'),
        ('financial', 'Financial'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='personal')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    # Metrics
    success_metric = models.CharField(max_length=300, help_text='How will you measure success?')
    target_value = models.FloatField(default=100.0, help_text='Numeric target (e.g. 100 for 100%)')
    current_value = models.FloatField(default=0.0)

    # Dates
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)

    skill = models.ForeignKey(
        'skills.UserSkill',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='goals',
        help_text='Optional skill this goal is helping to improve'
    )

    # AI metadata (stored as JSON for flexibility)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'target_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['target_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min(round((self.current_value / self.target_value) * 100, 1), 100)

    @property
    def days_remaining(self):
        delta = self.target_date - timezone.now().date()
        return delta.days

    @property
    def is_overdue(self):
        return self.days_remaining < 0 and self.status == 'active'

    @property
    def urgency_score(self):
        """
        Deadline urgency component (0–100) for the priority algorithm.
        Inverse of days remaining, capped at 100.
        """
        days = self.days_remaining
        if days <= 0:
            return 100
        elif days <= 3:
            return 90
        elif days <= 7:
            return 75
        elif days <= 14:
            return 55
        elif days <= 30:
            return 35
        else:
            return 15

    @property
    def importance_score(self):
        """Goal importance component (0–100) for the priority algorithm."""
        priority_map = {'high': 90, 'medium': 55, 'low': 20}
        return priority_map.get(self.priority, 55)

    def mark_completed(self):
        self.status = 'completed'
        self.current_value = self.target_value
        self.completed_at = timezone.now()
        self.save()


class Milestone(models.Model):
    """Checkpoints within a goal for granular progress tracking."""

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'target_date']

    def __str__(self):
        return f"{self.goal.title} → {self.title}"

    def complete(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
