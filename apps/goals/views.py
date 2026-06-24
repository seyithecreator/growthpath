"""
apps/goals/views.py
Main application views including the dashboard, goal CRUD, and analytics.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
import json

from .models import Goal, Milestone
from .forms import GoalForm, MilestoneForm
from .utils import compute_pgi
from .roadmap import RoadmapGenerator
from apps.activities.models import ActivityLog, ProductivitySnapshot
from apps.skills.models import UserSkill
from apps.priorities.engine import PriorityEngine
from apps.recommendations.engine import RecommendationEngine
from apps.recommendations.models import Recommendation as RecommendationRecord


@login_required
def dashboard(request):
    """Main dashboard — aggregates all data for the hero view."""
    user = request.user
    today = timezone.now().date()

    # ── Goals summary ────────────────────────────────────────────────────────
    active_goals = Goal.objects.filter(user=user, status='active')
    goal_stats = active_goals.aggregate(
        count=Count('id'),
        avg_progress=Avg('current_value'),
    )
    on_track = active_goals.filter(current_value__gte=50).count()

    # ── Activity this week ───────────────────────────────────────────────────
    week_start = today - timezone.timedelta(days=today.weekday())
    week_logs = ActivityLog.objects.filter(
        user=user, started_at__date__gte=week_start
    )
    hours_logged = week_logs.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    hours_logged = round(hours_logged / 60, 1)

    # ── Productivity snapshots for trend chart (last 7 days) ─────────────────
    snapshots = ProductivitySnapshot.objects.filter(
        user=user,
        date__gte=today - timezone.timedelta(days=6)
    ).order_by('date')

    trend_labels = []
    trend_data = []
    for snap in snapshots:
        trend_labels.append(snap.date.strftime('%a'))
        trend_data.append(round(snap.avg_productivity * 20, 1))  # scale 0-5 → 0-100

    # ── Priority engine ──────────────────────────────────────────────────────
    engine = PriorityEngine(user)
    top_priorities = engine.rank_goals()[:3]

    # ── AI recommendation (top 1 for dashboard teaser) ───────────────────────
    top_rec = user.recommendations.filter(is_read=False).order_by('rank').first()

    # ── Skills overview + radar data ─────────────────────────────────────────
    skills = UserSkill.objects.filter(user=user, is_active=True).select_related('domain')[:8]
    skills_count = skills.count()
    radar_labels = [s.domain.name for s in skills]
    radar_current = [s.current_score for s in skills]
    radar_target = [s.target_score for s in skills]

    # ── PGI ──────────────────────────────────────────────────────────────────
    pgi_score = compute_pgi(user)

    # ── Heatmap data (last 84 days / 12 weeks) ───────────────────────────────
    heatmap_start = today - timezone.timedelta(days=83)
    heatmap_snaps = ProductivitySnapshot.objects.filter(
        user=user, date__gte=heatmap_start
    ).values('date', 'avg_productivity')
    heatmap_data = {str(s['date']): round(s['avg_productivity'], 1) for s in heatmap_snaps}

    context = {
        'active_goals_count': goal_stats['count'] or 0,
        'on_track_count': on_track,
        'hours_logged': hours_logged,
        'skills_count': skills_count,
        'streak_days': user.streak_days,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'top_priorities': top_priorities,
        'top_rec': top_rec,
        'skills': skills,
        'today': today,
        'pgi_score': pgi_score,
        'radar_labels': json.dumps(radar_labels),
        'radar_current': json.dumps(radar_current),
        'radar_target': json.dumps(radar_target),
        'heatmap_data': json.dumps(heatmap_data),
        'heatmap_start': heatmap_start,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def goal_list(request):
    """List all goals with filtering by category and status."""
    user = request.user
    category = request.GET.get('category', '')
    status = request.GET.get('status', 'active')

    goals = Goal.objects.filter(user=user)
    if category:
        goals = goals.filter(category=category)
    if status:
        goals = goals.filter(status=status)

    # Annotate with milestone counts for sub-progress display
    goals = goals.prefetch_related('milestones')

    context = {
        'goals': goals,
        'category_filter': category,
        'status_filter': status,
        'categories': Goal.CATEGORY_CHOICES,
    }
    return render(request, 'goals/list.html', context)


@login_required
def goal_create(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, f'Goal "{goal.title}" created. Generate a roadmap to get started!')
            return redirect('goals:detail', pk=goal.pk)
    else:
        form = GoalForm()
    return render(request, 'goals/form.html', {'form': form, 'action': 'Create'})


@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    milestones = goal.milestones.all()
    activity_logs = goal.activity_logs.order_by('-started_at')[:10]
    completed_count = milestones.filter(is_completed=True).count()
    total_count = milestones.count()

    context = {
        'goal': goal,
        'milestones': milestones,
        'activity_logs': activity_logs,
        'milestone_form': MilestoneForm(),
        'completed_milestone_count': completed_count,
        'total_milestone_count': total_count,
    }
    return render(request, 'goals/detail.html', context)


@login_required
def goal_update(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated.')
            return redirect('goals:detail', pk=pk)
    else:
        form = GoalForm(instance=goal)
    return render(request, 'goals/form.html', {'form': form, 'action': 'Update', 'goal': goal})


@login_required
def goal_update_progress(request, pk):
    """AJAX endpoint to manually update goal progress value."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    try:
        new_value = float(request.POST.get('current_value', goal.current_value))
        goal.current_value = min(new_value, goal.target_value)
        if goal.current_value >= goal.target_value:
            goal.mark_completed()
        else:
            goal.save()
        return JsonResponse({
            'progress': goal.progress_percentage,
            'status': goal.status,
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid value'}, status=400)


@login_required
def complete_milestone(request, goal_pk, milestone_pk):
    """
    AJAX endpoint — toggles a milestone's is_completed state and
    recalculates goal progress proportionally.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    goal = get_object_or_404(Goal, pk=goal_pk, user=request.user)
    milestone = get_object_or_404(Milestone, pk=milestone_pk, goal=goal)

    # Toggle
    if milestone.is_completed:
        milestone.is_completed = False
        milestone.completed_at = None
        milestone.save()
    else:
        milestone.complete()

    # Recalculate goal progress based on milestones
    all_milestones = goal.milestones.all()
    total = all_milestones.count()
    completed = all_milestones.filter(is_completed=True).count()

    if total > 0:
        goal.current_value = round((completed / total) * goal.target_value, 2)
        if completed == total:
            goal.mark_completed()
        else:
            if goal.status == 'completed':
                goal.status = 'active'
                goal.completed_at = None
            goal.save()

    return JsonResponse({
        'progress': goal.progress_percentage,
        'milestone_count': total,
        'completed_count': completed,
        'milestone_completed': milestone.is_completed,
        'goal_status': goal.status,
    })


@login_required
def generate_roadmap(request, pk):
    """
    AJAX endpoint — generates milestone roadmap for a goal.
    Uses Gemini AI when a key is configured; falls back to
    template-based RoadmapGenerator automatically.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.conf import settings
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    # Remove existing incomplete milestones to start fresh
    goal.milestones.filter(is_completed=False).delete()

    milestone_defs = None

    # ── Try Gemini first ──────────────────────────────────────────────────────
    if settings.GEMINI_API_KEY:
        from .ai_client import GeminiClient
        raw = GeminiClient().generate_roadmap(goal, request.user)
        if raw:
            milestone_defs = []
            for m in raw:
                target_date = goal.start_date + timezone.timedelta(days=m['days_from_start'])
                milestone_defs.append({
                    'title': m['title'],
                    'description': m['description'],
                    'order': m['order'],
                    'target_date': target_date,
                })

    # ── Fall back to template-based generator ─────────────────────────────────
    if not milestone_defs:
        milestone_defs = RoadmapGenerator(goal).generate()

    created = []
    for m in milestone_defs:
        obj = Milestone.objects.create(
            goal=goal,
            title=m['title'],
            description=m['description'],
            order=m['order'],
            target_date=m['target_date'],
        )
        created.append({
            'id': obj.pk,
            'title': obj.title,
            'description': obj.description,
            'order': obj.order,
            'target_date': str(obj.target_date),
            'is_completed': obj.is_completed,
        })

    return JsonResponse({'milestones': created, 'count': len(created)})


VALID_REC_TYPES = {'deadline', 'skill_gap', 'habit', 'schedule', 'peer', 'resource'}


@login_required
def generate_recommendations(request, pk=None):
    """
    Trigger fresh recommendation generation.
    Uses Gemini AI when a key is configured; falls back to the
    rule-based + ML RecommendationEngine automatically.
    """
    from django.conf import settings
    user = request.user
    count = 0

    # ── Try Gemini first ──────────────────────────────────────────────────────
    if settings.GEMINI_API_KEY:
        from .ai_client import GeminiClient
        raw = GeminiClient().generate_recommendations(user)
        if raw:
            # Clear old unread recommendations before saving fresh ones
            RecommendationRecord.objects.filter(user=user, is_read=False).delete()
            for i, rec in enumerate(raw, start=1):
                rec_type = rec.get('type', 'resource')
                if rec_type not in VALID_REC_TYPES:
                    rec_type = 'resource'
                RecommendationRecord.objects.create(
                    user=user,
                    rec_type=rec_type,
                    rank=i,
                    title=str(rec.get('title', ''))[:300],
                    description=str(rec.get('description', '')),
                    action_label=str(rec.get('action_label', 'Take action'))[:100],
                    icon=str(rec.get('icon', 'ti-bulb'))[:50],
                    confidence=float(rec.get('confidence', 0.8)),
                    tags=[],
                )
            count = len(raw)

    # ── Fall back to rule-based + ML engine ───────────────────────────────────
    if count == 0:
        recs = RecommendationEngine(user).generate()
        count = len(recs)

    messages.success(request, f'{count} personalised recommendations generated.')
    return redirect(request.META.get('HTTP_REFERER', 'goals:dashboard'))
