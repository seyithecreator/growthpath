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

from .models import Goal, Milestone
from .forms import GoalForm, MilestoneForm
from apps.activities.models import ActivityLog, ProductivitySnapshot
from apps.skills.models import UserSkill
from apps.priorities.engine import PriorityEngine
from apps.recommendations.engine import RecommendationEngine


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
    if not top_rec:
        # Generate fresh recommendations asynchronously; show placeholder
        top_rec = None

    # ── Skills overview ──────────────────────────────────────────────────────
    skills = UserSkill.objects.filter(user=user, is_active=True).select_related('domain')[:8]
    skills_count = skills.count()

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
            messages.success(request, f'Goal "{goal.title}" created successfully.')
            return redirect('goals:detail', pk=goal.pk)
    else:
        form = GoalForm()
    return render(request, 'goals/form.html', {'form': form, 'action': 'Create'})


@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    milestones = goal.milestones.all()
    activity_logs = goal.activity_logs.order_by('-started_at')[:10]

    context = {
        'goal': goal,
        'milestones': milestones,
        'activity_logs': activity_logs,
        'milestone_form': MilestoneForm(),
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
    """AJAX endpoint to update goal progress value."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    try:
        new_value = float(request.POST.get('current_value', goal.current_value))
        goal.current_value = min(new_value, goal.target_value)
        if goal.current_value >= goal.target_value:
            goal.mark_completed()
            messages.success(request, f'🎉 Goal "{goal.title}" marked as completed!')
        else:
            goal.save()
        return JsonResponse({
            'progress': goal.progress_percentage,
            'status': goal.status,
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid value'}, status=400)


@login_required
def generate_recommendations(request, pk=None):
    """Trigger fresh recommendation generation for the user."""
    engine = RecommendationEngine(request.user)
    recs = engine.generate()
    messages.success(request, f'{len(recs)} recommendations generated.')
    return redirect(request.META.get('HTTP_REFERER', 'goals:dashboard'))
