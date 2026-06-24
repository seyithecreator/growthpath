"""apps/recommendations/models.py"""

from django.db import models
from django.conf import settings


class Recommendation(models.Model):

    REC_TYPE_CHOICES = [
        ('deadline', 'Deadline Alert'),
        ('skill_gap', 'Skill Gap'),
        ('habit', 'Habit Building'),
        ('schedule', 'Schedule Optimisation'),
        ('peer', 'Peer Insight'),
        ('resource', 'Resource Suggestion'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    goal = models.ForeignKey(
        'goals.Goal', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recommendations'
    )
    skill = models.ForeignKey(
        'skills.UserSkill', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recommendations'
    )

    rec_type = models.CharField(max_length=20, choices=REC_TYPE_CHOICES)
    rank = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=300)
    description = models.TextField()
    action_label = models.CharField(max_length=100, default='Take action')
    icon = models.CharField(max_length=50, default='ti-bulb')
    confidence = models.FloatField(default=1.0)

    tags = models.JSONField(default=list, blank=True)
    is_read = models.BooleanField(default=False)
    is_actioned = models.BooleanField(default=False)

    generated_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return f"[{self.rec_type}] {self.title[:60]}"
