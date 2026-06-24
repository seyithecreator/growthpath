"""
growthpath/celery_tasks.py
Async tasks for:
  - Daily productivity snapshot aggregation
  - Recommendation generation
  - Streak maintenance
  - Weekly report emails
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Sum, Count

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_daily_snapshots(self):
    """
    Celery beat task — runs nightly at 23:55.
    Aggregates all activity logs for today into ProductivitySnapshot.
    """
    from apps.activities.models import ActivityLog, ProductivitySnapshot

    today = timezone.now().date()
    users = User.objects.filter(is_active=True)
    created_count = 0

    for user in users:
        logs = ActivityLog.objects.filter(
            user=user,
            started_at__date=today
        )
        if not logs.exists():
            continue

        stats = logs.aggregate(
            total_sessions=Count('id'),
            total_minutes=Sum('duration_minutes'),
            avg_productivity=Avg('productivity_score'),
            avg_focus=Avg('focus_level'),
            goals_advanced=Count('goal', distinct=True),
            skills_practised=Count('skill', distinct=True),
        )

        ProductivitySnapshot.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'total_sessions': stats['total_sessions'] or 0,
                'total_minutes': stats['total_minutes'] or 0,
                'avg_productivity': round(stats['avg_productivity'] or 0, 2),
                'avg_focus': round(stats['avg_focus'] or 0, 2),
                'goals_advanced': stats['goals_advanced'] or 0,
                'skills_practised': stats['skills_practised'] or 0,
            }
        )
        created_count += 1

    logger.info("Daily snapshots generated for %d users", created_count)
    return created_count


@shared_task(bind=True, max_retries=3)
def refresh_user_recommendations(self, user_id: int):
    """
    Regenerates recommendations for a single user.
    Called after significant events (new goal, activity logged, skill updated).
    """
    from apps.recommendations.engine import RecommendationEngine
    try:
        user = User.objects.get(pk=user_id, is_active=True)
        engine = RecommendationEngine(user)
        recs = engine.generate()
        logger.info("Refreshed %d recommendations for user %d", len(recs), user_id)
        return len(recs)
    except User.DoesNotExist:
        logger.warning("User %d not found for recommendation refresh", user_id)
    except Exception as exc:
        logger.error("Recommendation refresh failed for user %d: %s", user_id, exc)
        self.retry(exc=exc, countdown=60)


@shared_task
def refresh_all_recommendations():
    """
    Celery beat task — runs every 6 hours.
    Refreshes recommendations for all active users with enough data.
    """
    from apps.activities.models import ActivityLog
    min_logs = 3
    active_user_ids = (
        ActivityLog.objects
        .values('user_id')
        .annotate(c=Count('id'))
        .filter(c__gte=min_logs)
        .values_list('user_id', flat=True)
    )
    for uid in active_user_ids:
        refresh_user_recommendations.delay(uid)
    logger.info("Queued recommendation refresh for %d users", len(active_user_ids))


@shared_task
def update_streaks():
    """
    Celery beat task — runs daily at midnight.
    Updates each user's streak_days field based on activity yesterday.
    """
    from apps.activities.models import ActivityLog

    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    today = timezone.now().date()
    active_yesterday = set(
        ActivityLog.objects
        .filter(started_at__date=yesterday)
        .values_list('user_id', flat=True)
        .distinct()
    )

    for user in User.objects.filter(is_active=True):
        if user.id in active_yesterday:
            user.streak_days += 1
            user.last_active_date = yesterday
            _check_streak_achievements(user)
        else:
            if user.last_active_date and (today - user.last_active_date).days > 1:
                user.streak_days = 0
        user.save(update_fields=['streak_days', 'last_active_date'])

    logger.info("Streaks updated for %d users", User.objects.filter(is_active=True).count())


def _check_streak_achievements(user):
    """Award streak-based achievements."""
    from apps.accounts.models import Achievement

    milestones = {7: '7-Day Streak', 14: '14-Day Streak', 30: '30-Day Streak', 100: 'Century Streak'}
    if user.streak_days in milestones:
        Achievement.objects.get_or_create(
            user=user,
            title=milestones[user.streak_days],
            defaults={
                'description': f"Maintained a {user.streak_days}-day learning streak!",
                'icon': 'ti-flame',
                'category': 'streak',
            }
        )
