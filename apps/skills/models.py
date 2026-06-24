"""
apps/skills/models.py
Skill domain tracking with assessments and historical score logging.
PostgreSQL JSONField used for flexible skill metadata.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class SkillDomain(models.Model):
    """Reusable skill domains (can be global or user-specific)."""

    DOMAIN_CHOICES = [
        ('technical', 'Technical'),
        ('academic', 'Academic'),
        ('soft_skills', 'Soft Skills'),
        ('leadership', 'Leadership'),
        ('creative', 'Creative'),
        ('health', 'Health & Fitness'),
    ]

    name = models.CharField(max_length=100)
    domain_type = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='ti-brain')
    color_hex = models.CharField(max_length=7, default='#2563EB')
    is_global = models.BooleanField(default=True)

    class Meta:
        ordering = ['domain_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_domain_type_display()})"


class UserSkill(models.Model):
    """
    A user's proficiency in a given skill domain.
    Score is 0–100. Metadata stored as JSON for extensibility.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    domain = models.ForeignKey(SkillDomain, on_delete=models.PROTECT, related_name='user_skills')
    current_score = models.FloatField(default=0.0)
    target_score = models.FloatField(default=80.0)

    # JSON metadata — flexible fields for Scikit-learn feature engineering
    metadata = models.JSONField(default=dict, blank=True)
    # Example metadata schema:
    # {
    #   "resources_used": ["Coursera", "YouTube"],
    #   "study_hours_total": 42,
    #   "last_assessment_method": "quiz",
    #   "confidence_level": "medium"
    # }

    last_assessed = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'domain')]
        ordering = ['-current_score']

    def __str__(self):
        return f"{self.user.username} — {self.domain.name}: {self.current_score}"

    @property
    def gap(self):
        return max(self.target_score - self.current_score, 0)

    @property
    def proficiency_label(self):
        s = self.current_score
        if s >= 85: return 'Expert'
        elif s >= 70: return 'Proficient'
        elif s >= 50: return 'Developing'
        elif s >= 30: return 'Beginner'
        return 'Novice'

    def update_score(self, new_score: float):
        """Update score and log the historical snapshot."""
        old = self.current_score
        self.current_score = round(min(max(new_score, 0), 100), 1)
        self.last_assessed = timezone.now().date()
        self.save()
        SkillScoreHistory.objects.create(
            skill=self,
            score=self.current_score,
            delta=round(self.current_score - old, 1)
        )


class SkillScoreHistory(models.Model):
    """
    Historical log of skill score changes — used by the ML engine
    to compute trend lines and predict future growth.
    """

    skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE, related_name='history')
    score = models.FloatField()
    delta = models.FloatField(default=0.0)    # positive = improvement
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['recorded_at']

    def __str__(self):
        sign = '+' if self.delta >= 0 else ''
        return f"{self.skill} → {self.score} ({sign}{self.delta})"
