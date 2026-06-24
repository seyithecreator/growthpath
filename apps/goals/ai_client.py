"""
apps/goals/ai_client.py
Google Gemini integration for personalized recommendations and roadmaps.
Falls back gracefully to rule-based engines when the key is missing or the
API call fails — the app always works regardless of API availability.
"""

import json
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum

logger = logging.getLogger(__name__)

VALID_REC_TYPES = {'deadline', 'skill_gap', 'habit', 'schedule', 'peer', 'resource'}

RECOMMENDATION_PROMPT = """\
You are a personal growth coach for Nigerian university students. \
Based on the student profile below, generate exactly 5 highly personalised, actionable recommendations.

{context}

Return a JSON array with exactly 5 objects. Each object must have these exact keys:
- "type": one of "deadline", "skill_gap", "habit", "schedule", "resource"
- "title": concise headline, max 60 characters
- "description": specific advice that references their actual goal or skill names, 2-3 sentences
- "action_label": short call-to-action for a button, max 25 characters (e.g. "Start today", "Review now", "Schedule it")
- "icon": a Tabler Icons CSS class (choose from: ti-book, ti-target, ti-clock, ti-brain, ti-run, \
ti-checklist, ti-chart-line, ti-calendar, ti-bulb, ti-alert-triangle, ti-flame, ti-award)
- "confidence": a float between 0.65 and 0.98

Rules:
- Reference actual goal titles and skill names from the profile — no generic advice
- Prioritise goals that are overdue or have under 50% progress with close deadlines
- Prioritise skills with the largest gaps between current and target score
- Write in second person ("You have…", "Focus on…", "Your…")
- Vary the recommendation types — do not repeat the same type twice
- Return ONLY the JSON array, no markdown, no explanation
"""

ROADMAP_PROMPT = """\
You are an academic growth coach helping a Nigerian university student achieve a specific goal. \
Create a realistic, step-by-step milestone roadmap tailored to this exact goal.

{context}

Return a JSON array of 6 to 8 milestone objects. Each must have these exact keys:
- "title": verb-first milestone title, max 80 characters, specific to THIS goal (not generic)
- "description": 1-2 concrete, actionable sentences explaining exactly what to do
- "order": integer starting at 1
- "days_from_start": integer — days from the goal start date when this milestone should be complete \
(must be between 1 and {total_days}, strictly increasing)

Rules:
- Milestones must be specific to THIS goal — no copy-paste generic steps
- First milestone must be completable within the first 20% of the timeline (≤ day {first_fifth})
- Final milestone must land 1-3 days before the deadline (day {near_end} to {total_days})
- Each milestone should build on the previous one logically
- Consider the student's university context and skill level when scoping effort
- Return ONLY the JSON array, no markdown, no explanation
"""


class GeminiClient:
    MODEL = 'gemini-1.5-flash'

    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                self.MODEL,
                generation_config={'response_mime_type': 'application/json', 'temperature': 0.75},
            )
        return self._model

    def _call(self, prompt):
        model = self._get_model()
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown fences if the model wraps the JSON
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text)

    # ── Context builders ──────────────────────────────────────────────────────

    def build_user_context(self, user):
        from apps.goals.models import Goal
        from apps.skills.models import UserSkill
        from apps.activities.models import ActivityLog

        goals = list(
            Goal.objects.filter(user=user, status='active')
            .prefetch_related('milestones')
            .order_by('target_date')[:8]
        )
        skills = list(
            UserSkill.objects.filter(user=user, is_active=True)
            .select_related('domain')
            .order_by('-gap')[:8]
        )

        two_weeks_ago = timezone.now() - timedelta(days=14)
        recent_logs = ActivityLog.objects.filter(user=user, started_at__gte=two_weeks_ago)
        stats = recent_logs.aggregate(
            avg_prod=Avg('productivity_score'),
            avg_focus=Avg('focus_level'),
            total_mins=Sum('duration_minutes'),
        )
        active_days = recent_logs.dates('started_at', 'day').count()

        lines = ['=== STUDENT PROFILE ===', f'Name: {user.display_name}']
        if user.university:
            lines.append(f'University: {user.university}')
        if user.department:
            lines.append(f'Department: {user.department}')
        if user.year_of_study:
            lines.append(f'Year of Study: {user.get_year_of_study_display()}')
        lines.append(f'Study streak: {user.streak_days} consecutive days')
        if user.peak_hour_start is not None:
            lines.append(f'Peak productivity window: {user.peak_hour_start}:00–{user.peak_hour_end}:00')

        lines.append(f'\n=== ACTIVE GOALS ({len(goals)}) ===')
        for g in goals:
            ms_total = g.milestones.count()
            ms_done = g.milestones.filter(is_completed=True).count()
            status_flag = ' ⚠ OVERDUE' if g.is_overdue else ''
            lines.append(
                f'• "{g.title}" [{g.category} / {g.priority} priority]'
                f'{status_flag}'
            )
            lines.append(
                f'  Progress: {g.progress_percentage:.0f}% | '
                f'Deadline: {g.target_date} ({g.days_remaining} days left)'
            )
            lines.append(f'  Success metric: {g.success_metric}')
            if ms_total:
                lines.append(f'  Milestones: {ms_done}/{ms_total} completed')

        lines.append(f'\n=== SKILLS ({len(skills)}) ===')
        for s in skills:
            lines.append(
                f'• {s.domain.name}: {s.current_score:.0f}/100 '
                f'(target {s.target_score:.0f}, gap {s.gap:.0f} pts, {s.proficiency_label})'
            )

        lines.append(f'\n=== RECENT ACTIVITY (last 14 days) ===')
        lines.append(f'Days with activity: {active_days}/14')
        if stats['avg_prod']:
            lines.append(f'Average productivity: {stats["avg_prod"]:.1f}/5')
            lines.append(f'Average focus: {stats["avg_focus"]:.1f}/5')
        if stats['total_mins']:
            h, m = divmod(int(stats['total_mins']), 60)
            lines.append(f'Total study time: {h}h {m}m')

        return '\n'.join(lines)

    def build_goal_context(self, goal, user):
        from apps.skills.models import UserSkill

        total_days = max((goal.target_date - goal.start_date).days, 1)
        skills = list(
            UserSkill.objects.filter(user=user, is_active=True)
            .select_related('domain')
            .order_by('-current_score')[:5]
        )

        lines = [
            '=== GOAL ===',
            f'Title: "{goal.title}"',
            f'Category: {goal.get_category_display()}',
            f'Priority: {goal.priority}',
        ]
        if goal.description:
            lines.append(f'Description: {goal.description}')
        lines.append(f'Success metric: {goal.success_metric}')
        lines.append(f'Start date: {goal.start_date}')
        lines.append(f'Deadline: {goal.target_date} ({total_days} days total timeline)')
        lines.append(f'Current progress: {goal.progress_percentage:.0f}%')

        lines.append('\n=== STUDENT ===')
        lines.append(f'Name: {user.display_name}')
        if user.university:
            lines.append(f'University: {user.university}, {user.department}')
        if user.year_of_study:
            lines.append(f'Year: {user.get_year_of_study_display()}')

        if skills:
            lines.append('\nSkills:')
            for s in skills:
                lines.append(f'• {s.domain.name}: {s.current_score:.0f}/100 ({s.proficiency_label})')

        return '\n'.join(lines)

    # ── Public generation methods ─────────────────────────────────────────────

    def generate_recommendations(self, user):
        """
        Returns list of up to 5 dicts, or None on failure.
        Each dict has: type, title, description, action_label, icon, confidence
        """
        try:
            context = self.build_user_context(user)
            prompt = RECOMMENDATION_PROMPT.format(context=context)
            data = self._call(prompt)
            if not isinstance(data, list) or not data:
                raise ValueError('Expected non-empty JSON array')
            return data[:5]
        except Exception as exc:
            logger.warning('Gemini recommendations failed: %s', exc)
            return None

    def generate_roadmap(self, goal, user):
        """
        Returns list of 6-8 dicts, or None on failure.
        Each dict has: title, description, order, days_from_start
        """
        try:
            total_days = max((goal.target_date - goal.start_date).days, 7)
            context = self.build_goal_context(goal, user)
            prompt = ROADMAP_PROMPT.format(
                context=context,
                total_days=total_days,
                first_fifth=max(1, total_days // 5),
                near_end=max(1, total_days - 3),
            )
            data = self._call(prompt)
            if not isinstance(data, list) or not data:
                raise ValueError('Expected non-empty JSON array')

            cleaned = []
            prev_days = 0
            for i, m in enumerate(data[:8], start=1):
                raw_days = int(m.get('days_from_start', total_days * i // max(len(data), 1)))
                days = max(prev_days + 1, min(raw_days, total_days))
                prev_days = days
                cleaned.append({
                    'title': str(m.get('title', f'Milestone {i}'))[:80],
                    'description': str(m.get('description', ''))[:500],
                    'order': i,
                    'days_from_start': days,
                })
            return cleaned
        except Exception as exc:
            logger.warning('Gemini roadmap failed: %s', exc)
            return None
