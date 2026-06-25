import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from itertools import groupby

from .models import ActivityLog, ProductivitySnapshot


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

    return render(request, 'activities/log.html', {
        'grouped_logs': grouped_logs,
        'calendar_weeks': calendar_weeks,
        'heatmap_data': json.dumps(heatmap_data),
        'activity_type_icons': ACTIVITY_TYPE_ICONS,
        'active_nav': 'activities',
        'today': today,
    })
