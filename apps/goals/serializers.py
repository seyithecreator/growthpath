"""
REST API Serializers — GrowthPath
Covers: Goals, Skills, Activities, Priorities, Recommendations
"""

from rest_framework import serializers
from apps.goals.models import Goal, Milestone
from apps.skills.models import UserSkill, SkillDomain, SkillScoreHistory
from apps.activities.models import ActivityLog, ProductivitySnapshot
from apps.recommendations.models import Recommendation
from apps.accounts.models import User, Achievement


# ─── Accounts ────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'display_name', 'initials', 'university', 'department',
            'year_of_study', 'streak_days', 'total_points',
            'daily_reminder', 'weekly_report', 'ai_personalisation',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'streak_days', 'total_points']


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'icon', 'category', 'unlocked_at']


# ─── Goals ───────────────────────────────────────────────────────────────────

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = [
            'id', 'title', 'description', 'target_date',
            'is_completed', 'completed_at', 'order'
        ]


class GoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    urgency_score = serializers.ReadOnlyField()
    milestones = MilestoneSerializer(many=True, read_only=True)
    milestone_count = serializers.SerializerMethodField()
    completed_milestones = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'category', 'priority', 'status',
            'success_metric', 'target_value', 'current_value',
            'progress_percentage', 'days_remaining', 'is_overdue',
            'urgency_score', 'start_date', 'target_date', 'completed_at',
            'tags', 'notes', 'milestones', 'milestone_count',
            'completed_milestones', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']

    def get_milestone_count(self, obj):
        return obj.milestones.count()

    def get_completed_milestones(self, obj):
        return obj.milestones.filter(is_completed=True).count()

    def validate_target_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Target date cannot be in the past.")
        return value


class GoalCreateSerializer(GoalSerializer):
    """Slim serializer for creation (excludes read-only nested data)."""
    class Meta(GoalSerializer.Meta):
        fields = [
            'title', 'description', 'category', 'priority',
            'success_metric', 'target_value', 'target_date', 'tags', 'notes'
        ]


# ─── Skills ──────────────────────────────────────────────────────────────────

class SkillDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillDomain
        fields = ['id', 'name', 'domain_type', 'description', 'icon', 'color_hex']


class SkillScoreHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillScoreHistory
        fields = ['id', 'score', 'delta', 'recorded_at', 'notes']


class UserSkillSerializer(serializers.ModelSerializer):
    domain = SkillDomainSerializer(read_only=True)
    domain_id = serializers.PrimaryKeyRelatedField(
        queryset=SkillDomain.objects.all(), source='domain', write_only=True
    )
    gap = serializers.ReadOnlyField()
    proficiency_label = serializers.ReadOnlyField()
    history = SkillScoreHistorySerializer(many=True, read_only=True)

    class Meta:
        model = UserSkill
        fields = [
            'id', 'domain', 'domain_id', 'current_score', 'target_score',
            'gap', 'proficiency_label', 'metadata', 'last_assessed',
            'notes', 'is_active', 'history', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_assessed', 'created_at', 'updated_at']


# ─── Activities ──────────────────────────────────────────────────────────────

class ActivityLogSerializer(serializers.ModelSerializer):
    goal_title = serializers.SerializerMethodField()
    skill_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'activity_type', 'title', 'description',
            'started_at', 'ended_at', 'duration_minutes',
            'productivity_score', 'focus_level', 'outcome_notes',
            'goal', 'goal_title', 'skill', 'skill_name',
            'goal_progress_delta', 'skill_score_delta',
            'tags', 'logged_at',
        ]
        read_only_fields = ['id', 'logged_at']

    def get_goal_title(self, obj):
        return obj.goal.title if obj.goal else None

    def get_skill_name(self, obj):
        return obj.skill.domain.name if obj.skill else None

    def validate(self, data):
        if data.get('ended_at') and data.get('started_at'):
            if data['ended_at'] < data['started_at']:
                raise serializers.ValidationError("End time must be after start time.")
        return data


class ProductivitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductivitySnapshot
        fields = [
            'date', 'total_sessions', 'total_minutes',
            'avg_productivity', 'avg_focus', 'goals_advanced',
            'skills_practised', 'predicted_next_day_score',
        ]


# ─── Recommendations ─────────────────────────────────────────────────────────

class RecommendationSerializer(serializers.ModelSerializer):
    goal_title = serializers.SerializerMethodField()
    skill_name = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            'id', 'rec_type', 'rank', 'title', 'description', 'action_label',
            'icon', 'confidence', 'tags', 'is_read', 'is_actioned',
            'goal', 'goal_title', 'skill', 'skill_name', 'generated_at',
        ]
        read_only_fields = ['id', 'generated_at', 'rank', 'confidence']

    def get_goal_title(self, obj):
        return obj.goal.title if obj.goal else None

    def get_skill_name(self, obj):
        return obj.skill.domain.name if obj.skill else None
