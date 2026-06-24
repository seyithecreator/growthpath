from django.utils import timezone
from django.db.models import Sum


def compute_pgi(user):
    """
    Personal Growth Index (0–100): weighted composite of skill attainment,
    goal progress, consistency streak, and weekly engagement.
    """
    from apps.skills.models import UserSkill
    from apps.activities.models import ActivityLog
    from .models import Goal

    # ── Skills attainment (35%): avg ratio of current/target per active skill ─
    skills = list(UserSkill.objects.filter(user=user, is_active=True))
    if skills:
        ratios = [min(s.current_score / s.target_score, 1.0) * 100
                  for s in skills if s.target_score > 0]
        skill_score = sum(ratios) / len(ratios) if ratios else 0.0
    else:
        skill_score = 0.0

    # ── Goal progress (35%): avg progress_percentage across non-abandoned goals ─
    goals = list(Goal.objects.filter(user=user).exclude(status='abandoned'))
    goal_score = (sum(g.progress_percentage for g in goals) / len(goals)) if goals else 0.0

    # ── Consistency (20%): streak normalised to 30 days ──────────────────────
    consistency_score = min(user.streak_days / 30.0, 1.0) * 100

    # ── Engagement (10%): this-week minutes normalised to 10 h target ─────────
    today = timezone.now().date()
    week_start = today - timezone.timedelta(days=today.weekday())
    weekly_minutes = ActivityLog.objects.filter(
        user=user, started_at__date__gte=week_start
    ).aggregate(total=Sum('duration_minutes'))['total'] or 0
    engagement_score = min(weekly_minutes / 600.0, 1.0) * 100

    pgi = round(
        (skill_score * 0.35) +
        (goal_score * 0.35) +
        (consistency_score * 0.20) +
        (engagement_score * 0.10),
        1
    )
    return pgi
