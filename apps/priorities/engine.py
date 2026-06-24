"""
apps/priorities/engine.py
──────────────────────────────────────────────────────────────────────────────
Priority-Setting Algorithm
──────────────────────────────────────────────────────────────────────────────
Dynamically ranks user goals and tasks using a weighted composite score:

    Priority Score = (0.40 × Deadline Urgency)
                   + (0.35 × Goal Importance)
                   + (0.25 × Historical Completion Rate)

All components are normalised to 0–100.

References:
    McKinney, W. (2017). Python for Data Analysis. O'Reilly Media.
    NumPy & Pandas used for vectorised computation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Weight constants (configurable via settings) ─────────────────────────────

WEIGHTS = settings.RECOMMENDATION_ENGINE.get('PRIORITY_WEIGHTS', {
    'deadline_urgency': 0.40,
    'goal_importance': 0.35,
    'completion_rate': 0.25,
})


@dataclass
class PriorityItem:
    """Represents a ranked goal with its component scores."""
    goal_id: int
    title: str
    category: str
    target_date: date
    priority_level: str           # high / medium / low
    current_progress: float       # 0–100

    # Component scores (0–100)
    urgency_score: float = 0.0
    importance_score: float = 0.0
    completion_rate_score: float = 0.0
    composite_score: float = 0.0

    urgency_label: str = 'Low'
    days_remaining: int = 0
    rank: int = 0

    tags: List[str] = field(default_factory=list)


class PriorityEngine:
    """
    Computes priority rankings for a user's active goals.

    Usage:
        engine = PriorityEngine(user)
        ranked = engine.rank_goals()
    """

    def __init__(self, user):
        self.user = user
        self.today = date.today()

    # ─── Public API ──────────────────────────────────────────────────────────

    def rank_goals(self) -> List[PriorityItem]:
        """Return all active goals ranked by composite priority score."""
        from apps.goals.models import Goal

        goals = Goal.objects.filter(
            user=self.user, status='active'
        ).prefetch_related('milestones', 'activity_logs')

        if not goals.exists():
            return []

        completion_rates = self._compute_completion_rates(goals)
        items = []

        for goal in goals:
            urgency = self._deadline_urgency(goal.target_date)
            importance = self._importance_score(goal.priority)
            hist_rate = completion_rates.get(goal.id, 50.0)

            composite = round(
                (WEIGHTS['deadline_urgency'] * urgency) +
                (WEIGHTS['goal_importance'] * importance) +
                (WEIGHTS['completion_rate'] * hist_rate),
                1
            )

            items.append(PriorityItem(
                goal_id=goal.id,
                title=goal.title,
                category=goal.category,
                target_date=goal.target_date,
                priority_level=goal.priority,
                current_progress=goal.progress_percentage,
                urgency_score=urgency,
                importance_score=importance,
                completion_rate_score=hist_rate,
                composite_score=composite,
                urgency_label=self._urgency_label(urgency),
                days_remaining=(goal.target_date - self.today).days,
                tags=goal.tags or [],
            ))

        # Sort descending by composite score, assign ranks
        items.sort(key=lambda x: x.composite_score, reverse=True)
        for i, item in enumerate(items, start=1):
            item.rank = i

        logger.info(
            "Priority ranking computed for user %s: %d goals ranked",
            self.user.id, len(items)
        )
        return items

    def to_dataframe(self) -> pd.DataFrame:
        """Return rankings as a Pandas DataFrame for analysis / export."""
        items = self.rank_goals()
        if not items:
            return pd.DataFrame()

        records = [
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
                'current_progress_%': i.current_progress,
                'urgency_label': i.urgency_label,
            }
            for i in items
        ]
        return pd.DataFrame(records)

    # ─── Component scorers ───────────────────────────────────────────────────

    @staticmethod
    def _deadline_urgency(target_date: date) -> float:
        """
        Urgency score based on days until deadline.
        Uses an exponential decay curve: closer = higher score.

        Score = 100 × e^(−0.05 × max(days, 0))  clamped to [0, 100]
        """
        days = (target_date - date.today()).days
        if days <= 0:
            return 100.0
        score = 100 * np.exp(-0.05 * days)
        return round(float(np.clip(score, 0, 100)), 1)

    @staticmethod
    def _importance_score(priority: str) -> float:
        """Map priority label to numeric importance score."""
        return {'high': 90.0, 'medium': 55.0, 'low': 20.0}.get(priority, 55.0)

    def _compute_completion_rates(self, goals) -> dict:
        """
        Historical completion rate for each goal, derived from activity logs.
        Rate = (sessions with positive delta / total sessions) × 100.
        Falls back to 50.0 if no history.
        """
        from apps.activities.models import ActivityLog

        goal_ids = [g.id for g in goals]
        logs = ActivityLog.objects.filter(
            user=self.user,
            goal_id__in=goal_ids
        ).values('goal_id', 'goal_progress_delta')

        # Vectorise with Pandas
        if not logs:
            return {gid: 50.0 for gid in goal_ids}

        df = pd.DataFrame(list(logs))
        if df.empty:
            return {gid: 50.0 for gid in goal_ids}

        grouped = df.groupby('goal_id').apply(
            lambda g: round(
                (g['goal_progress_delta'] > 0).sum() / len(g) * 100, 1
            )
        )
        rates = grouped.to_dict()

        # Fill missing goals with default
        return {gid: rates.get(gid, 50.0) for gid in goal_ids}

    @staticmethod
    def _urgency_label(score: float) -> str:
        if score >= 80: return 'Critical'
        elif score >= 60: return 'High'
        elif score >= 40: return 'Medium'
        return 'Low'
