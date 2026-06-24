"""
REST API ViewSets — GrowthPath
Full CRUD + custom actions for all modules.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Sum, Count

from apps.goals.models import Goal, Milestone
from apps.skills.models import UserSkill, SkillDomain
from apps.activities.models import ActivityLog, ProductivitySnapshot
from apps.recommendations.models import Recommendation
from apps.priorities.engine import PriorityEngine
from apps.recommendations.engine import RecommendationEngine
from .serializers import (
    GoalSerializer, GoalCreateSerializer, MilestoneSerializer,
    UserSkillSerializer, SkillDomainSerializer,
    ActivityLogSerializer, ProductivitySnapshotSerializer,
    RecommendationSerializer, UserSerializer,
)

User = get_user_model()


# ─── Auth ────────────────────────────────────────────────────────────────────

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'display_name': user.display_name,
        })


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timezone.timedelta(days=today.weekday())

        active_goals = Goal.objects.filter(user=user, status='active')
        week_logs = ActivityLog.objects.filter(
            user=user, started_at__date__gte=week_start
        )
        snapshots = ProductivitySnapshot.objects.filter(
            user=user,
            date__gte=today - timezone.timedelta(days=6)
        ).order_by('date')

        return Response({
            'active_goals': active_goals.count(),
            'on_track': active_goals.filter(current_value__gte=50).count(),
            'hours_logged_week': round(
                (week_logs.aggregate(t=Sum('duration_minutes'))['t'] or 0) / 60, 1
            ),
            'streak_days': user.streak_days,
            'skills_count': UserSkill.objects.filter(user=user, is_active=True).count(),
            'trend': [
                {'date': s.date.isoformat(), 'score': round(s.avg_productivity * 20, 1)}
                for s in snapshots
            ],
        })


# ─── Goals ───────────────────────────────────────────────────────────────────

class GoalViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Goal.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        category = self.request.query_params.get('category')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        return GoalSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        goal = self.get_object()
        new_value = request.data.get('current_value')
        if new_value is None:
            return Response({'error': 'current_value required'}, status=400)
        goal.current_value = min(float(new_value), goal.target_value)
        if goal.current_value >= goal.target_value:
            goal.mark_completed()
        else:
            goal.save()
        return Response({
            'progress_percentage': goal.progress_percentage,
            'status': goal.status,
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        goal = self.get_object()
        goal.mark_completed()
        return Response({'status': 'completed', 'completed_at': goal.completed_at})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        goals = self.get_queryset()
        return Response({
            'total': goals.count(),
            'by_status': dict(goals.values_list('status').annotate(c=Count('id')).values_list('status', 'c')),
            'by_category': dict(goals.values_list('category').annotate(c=Count('id')).values_list('category', 'c')),
            'avg_progress': round(goals.aggregate(a=Avg('current_value'))['a'] or 0, 1),
        })


# ─── Skills ──────────────────────────────────────────────────────────────────

class UserSkillViewSet(viewsets.ModelViewSet):
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(
            user=self.request.user, is_active=True
        ).select_related('domain').prefetch_related('history')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_score(self, request, pk=None):
        skill = self.get_object()
        new_score = request.data.get('score')
        if new_score is None:
            return Response({'error': 'score required'}, status=400)
        skill.update_score(float(new_score))
        return Response({'current_score': skill.current_score, 'gap': skill.gap})

    @action(detail=False, methods=['get'])
    def radar_data(self, request):
        """Radar chart data for the frontend."""
        skills = self.get_queryset()
        return Response({
            'labels': [s.domain.name for s in skills],
            'current': [s.current_score for s in skills],
            'target': [s.target_score for s in skills],
        })


# ─── Activities ──────────────────────────────────────────────────────────────

class ActivityLogViewSet(viewsets.ModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ActivityLog.objects.filter(user=self.request.user)
        days = self.request.query_params.get('days')
        if days:
            cutoff = timezone.now() - timezone.timedelta(days=int(days))
            qs = qs.filter(started_at__gte=cutoff)
        return qs

    def perform_create(self, serializer):
        log = serializer.save(user=self.request.user)
        # Apply progress delta to linked goal
        if log.goal and log.goal_progress_delta:
            log.goal.current_value = min(
                log.goal.current_value + log.goal_progress_delta,
                log.goal.target_value
            )
            log.goal.save()
        # Apply skill score delta to linked skill
        if log.skill and log.skill_score_delta:
            log.skill.update_score(log.skill.current_score + log.skill_score_delta)


# ─── Priorities ──────────────────────────────────────────────────────────────

class PriorityViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        engine = PriorityEngine(request.user)
        items = engine.rank_goals()
        data = [
            {
                'rank': i.rank,
                'goal_id': i.goal_id,
                'title': i.title,
                'category': i.category,
                'days_remaining': i.days_remaining,
                'urgency_score': i.urgency_score,
                'importance_score': i.importance_score,
                'completion_rate_score': i.completion_rate_score,
                'composite_score': i.composite_score,
                'urgency_label': i.urgency_label,
                'current_progress': i.current_progress,
            }
            for i in items
        ]
        return Response(data)


# ─── Recommendations ─────────────────────────────────────────────────────────

class RecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Use /generate/ to create recommendations.'}, status=405)

    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        engine = RecommendationEngine(request.user)
        recs = engine.generate()
        qs = self.get_queryset()
        return Response(RecommendationSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        rec = self.get_object()
        rec.is_read = True
        rec.read_at = timezone.now()
        rec.save()
        return Response({'status': 'read'})

    @action(detail=True, methods=['post'])
    def mark_actioned(self, request, pk=None):
        rec = self.get_object()
        rec.is_actioned = True
        rec.save()
        return Response({'status': 'actioned'})
