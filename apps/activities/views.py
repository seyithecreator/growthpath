import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from itertools import groupby

from .models import ActivityLog, ProductivitySnapshot
from apps.goals.models import Goal
from apps.skills.models import UserSkill


ACTIVITY_TYPE_ICONS = {
    'study': 'ti-book',
    'exercise': 'ti-run',
    'reading': 'ti-book-2',
    'project': 'ti-code',
    'assessment': 'ti-clipboard-check',
    'networking': 'ti-users',
    'reflection': 'ti-pencil',
    'workshop': 'ti-chalkboard',
    'other': 'ti-dots',
}


@login_required
def activity_log(request):
    user = request.user
    today = timezone.now().date()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        activity_type = request.POST.get('activity_type', 'study')
        duration = request.POST.get('duration_minutes', '30')
        productivity = request.POST.get('productivity_score', '3')
        focus = request.POST.get('focus_level', '3')
        goal_id = request.POST.get('goal_id') or None
        outcome = request.POST.get('outcome_notes', '')

        if title:
            try:
                goal_obj = Goal.objects.get(pk=goal_id, user=user) if goal_id else None
            except Goal.DoesNotExist:
                goal_obj = None

            started_at = timezone.now()
            ActivityLog.objects.create(
                user=user,
                title=title,
                activity_type=activity_type,
                duration_minutes=int(duration),
                productivity_score=int(productivity),
                focus_level=int(focus),
                outcome_notes=outcome,
                goal=goal_obj,
                started_at=started_at,
                ended_at=started_at + timezone.timedelta(minutes=int(duration)),
            )
            messages.success(request, 'Activity logged.')
        return redirect('activities:log')

    # Recent logs (last 30 days), grouped by date
    logs = list(
        ActivityLog.objects.filter(
            user=user,
            started_at__date__gte=today - timezone.timedelta(days=29)
        ).select_related('goal').order_by('-started_at__date', '-started_at')
    )

    grouped_logs = []
    for date_val, group in groupby(logs, key=lambda l: l.started_at.date()):
        grouped_logs.append({'date': date_val, 'logs': list(group)})

    # 52-week heatmap data
    heatmap_start = today - timezone.timedelta(weeks=52)
    snaps = ProductivitySnapshot.objects.filter(
        user=user, date__gte=heatmap_start
    ).values('date', 'avg_productivity')
    heatmap_data = {str(s['date']): round(s['avg_productivity'], 1) for s in snaps}

    # Build 52-week calendar grid (Sunday-first weeks)
    grid_start = heatmap_start
    # Rewind to nearest Sunday
    grid_start -= timezone.timedelta(days=grid_start.weekday() + 1)
    calendar_weeks = []
    cursor = grid_start
    while cursor <= today + timezone.timedelta(days=6):
        week = []
        for _ in range(7):
            week.append({
                'date': str(cursor),
                'score': heatmap_data.get(str(cursor), 0),
                'future': cursor > today,
            })
            cursor += timezone.timedelta(days=1)
        calendar_weeks.append(week)

    active_goals = Goal.objects.filter(user=user, status='active')
    activity_types = ActivityLog.ACTIVITY_TYPE_CHOICES

    return render(request, 'activities/log.html', {
        'grouped_logs': grouped_logs,
        'calendar_weeks': calendar_weeks,
        'heatmap_data': json.dumps(heatmap_data),
        'active_goals': active_goals,
        'activity_types': activity_types,
        'activity_type_icons': ACTIVITY_TYPE_ICONS,
        'active_nav': 'activities',
        'today': today,
    })
