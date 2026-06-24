"""
apps/recommendations/engine.py
──────────────────────────────────────────────────────────────────────────────
GrowthPath Recommendation Engine
──────────────────────────────────────────────────────────────────────────────
Generates personalised next-action recommendations using:

  1. Rule-based heuristics (fast, always available)
  2. Scikit-learn Random Forest classifier for user-behaviour patterns
  3. Collaborative filtering via cosine similarity (peer comparisons)

References:
    Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python.
    McKinney, W. (2017). Python for Data Analysis. O'Reilly Media.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_RECS = settings.RECOMMENDATION_ENGINE.get('MAX_RECOMMENDATIONS', 5)
MIN_LOGS = settings.RECOMMENDATION_ENGINE.get('MIN_ACTIVITY_LOGS', 3)


@dataclass
class Recommendation:
    """A single personalised recommendation."""
    rec_type: str                   # skill_gap | deadline | habit | peer | schedule
    priority: int                   # 1 = highest
    title: str
    description: str
    action_label: str
    goal_id: Optional[int] = None
    skill_id: Optional[int] = None
    icon: str = 'ti-bulb'
    confidence: float = 1.0         # 0–1, from ML model
    tags: List[str] = field(default_factory=list)


class RecommendationEngine:
    """
    Main engine. Call `.generate()` to get ranked recommendations.

    Usage:
        engine = RecommendationEngine(user)
        recs = engine.generate()
    """

    def __init__(self, user):
        self.user = user
        self.today = date.today()
        self._activity_df: Optional[pd.DataFrame] = None
        self._goals = None
        self._skills = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def generate(self) -> List[Recommendation]:
        """Generate and rank all recommendation types."""
        self._load_data()
        recs: List[Recommendation] = []

        # Layer 1: Rule-based (always run)
        recs += self._deadline_recommendations()
        recs += self._skill_gap_recommendations()
        recs += self._habit_recommendations()

        # Layer 2: ML-based (run if enough data)
        if self._has_enough_data():
            recs += self._ml_schedule_recommendations()
            recs += self._collaborative_recommendations()

        # Rank, deduplicate, cap
        recs = self._rank_and_filter(recs)

        # Persist to DB
        self._save_recommendations(recs)

        logger.info(
            "Generated %d recommendations for user %s", len(recs), self.user.id
        )
        return recs

    # ─── Data loading ────────────────────────────────────────────────────────

    def _load_data(self):
        from apps.goals.models import Goal
        from apps.skills.models import UserSkill
        from apps.activities.models import ActivityLog

        self._goals = Goal.objects.filter(user=self.user, status='active')
        self._skills = UserSkill.objects.filter(
            user=self.user, is_active=True
        ).select_related('domain')

        logs = ActivityLog.objects.filter(user=self.user).values(
            'id', 'activity_type', 'started_at', 'duration_minutes',
            'productivity_score', 'focus_level', 'goal_id', 'skill_id',
            'goal_progress_delta'
        )
        self._activity_df = pd.DataFrame(list(logs)) if logs else pd.DataFrame()

        if not self._activity_df.empty:
            self._activity_df['started_at'] = pd.to_datetime(
                self._activity_df['started_at']
            )
            self._activity_df['hour'] = self._activity_df['started_at'].dt.hour
            self._activity_df['day_of_week'] = self._activity_df['started_at'].dt.dayofweek
            self._activity_df['date'] = self._activity_df['started_at'].dt.date

    def _has_enough_data(self) -> bool:
        return (
            self._activity_df is not None
            and len(self._activity_df) >= MIN_LOGS
        )

    # ─── Rule-based recommenders ─────────────────────────────────────────────

    def _deadline_recommendations(self) -> List[Recommendation]:
        """Recommend action on goals with approaching deadlines."""
        recs = []
        for goal in self._goals:
            days = (goal.target_date - self.today).days
            if 0 <= days <= 7 and goal.progress_percentage < 80:
                recs.append(Recommendation(
                    rec_type='deadline',
                    priority=1,
                    title=f"Urgent: '{goal.title}' is due in {days} day{'s' if days != 1 else ''}",
                    description=(
                        f"You are at {goal.progress_percentage:.0f}% and the deadline is "
                        f"{goal.target_date.strftime('%d %b %Y')}. "
                        f"Focus sessions today can close this gap."
                    ),
                    action_label='Log a session',
                    goal_id=goal.id,
                    icon='ti-alarm',
                    confidence=1.0,
                    tags=['deadline', goal.category],
                ))
        return recs

    def _skill_gap_recommendations(self) -> List[Recommendation]:
        """Flag skills where current score is far below target."""
        recs = []
        for skill in self._skills:
            gap = skill.gap
            if gap >= 20:
                recs.append(Recommendation(
                    rec_type='skill_gap',
                    priority=2,
                    title=f"Close your {skill.domain.name} skill gap",
                    description=(
                        f"Your {skill.domain.name} score is {skill.current_score:.0f}/100 — "
                        f"{gap:.0f} points below your target of {skill.target_score:.0f}. "
                        f"Dedicated practice of 1–2 hours/day can close this in "
                        f"{max(1, int(gap / 3))} weeks."
                    ),
                    action_label='Find resources',
                    skill_id=skill.id,
                    icon='ti-trending-up',
                    confidence=0.9,
                    tags=['skill', skill.domain.domain_type],
                ))
        return recs[:2]   # cap at 2 skill-gap recommendations

    def _habit_recommendations(self) -> List[Recommendation]:
        """Detect consistency gaps and suggest habit building."""
        recs = []
        if self._activity_df is None or self._activity_df.empty:
            return recs

        df = self._activity_df
        last_7_days = [self.today - timedelta(days=i) for i in range(7)]
        active_days = set(df['date'].tolist())
        missed = [d for d in last_7_days if d not in active_days]

        if len(missed) >= 3:
            recs.append(Recommendation(
                rec_type='habit',
                priority=3,
                title='Re-establish your daily learning habit',
                description=(
                    f"You missed {len(missed)} of the last 7 days. "
                    "Consistency is the strongest predictor of long-term growth. "
                    "Start with a 20-minute session today to rebuild momentum."
                ),
                action_label='Log a quick session',
                icon='ti-flame',
                confidence=0.85,
                tags=['habit', 'consistency'],
            ))
        return recs

    # ─── ML-based recommenders ───────────────────────────────────────────────

    def _ml_schedule_recommendations(self) -> List[Recommendation]:
        """
        Use a Random Forest to predict the user's peak productivity hour.
        Features: hour_of_day, day_of_week, duration_minutes, activity_type_enc
        Target: productivity_score >= 4 (binary: high vs low productivity)
        """
        recs = []
        df = self._activity_df.copy()

        if len(df) < MIN_LOGS:
            return recs

        # Feature engineering
        df['activity_type_enc'] = df['activity_type'].astype('category').cat.codes
        df['high_productivity'] = (df['productivity_score'] >= 4).astype(int)

        feature_cols = ['hour', 'day_of_week', 'duration_minutes', 'activity_type_enc']
        X = df[feature_cols].fillna(0)
        y = df['high_productivity']

        if y.nunique() < 2:
            return recs   # need both classes to train

        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            clf = RandomForestClassifier(
                n_estimators=50,
                max_depth=4,
                random_state=42,
                class_weight='balanced'
            )
            clf.fit(X_scaled, y)

            # Predict across all 24 hours for tomorrow (next weekday)
            tomorrow_dow = (self.today.weekday() + 1) % 7
            hours = np.arange(6, 23)
            test_features = np.column_stack([
                hours,
                np.full(len(hours), tomorrow_dow),
                np.full(len(hours), 60),    # assume 60-min session
                np.zeros(len(hours)),
            ])
            test_scaled = scaler.transform(test_features)
            probs = clf.predict_proba(test_scaled)[:, 1]

            best_hour_idx = int(np.argmax(probs))
            best_hour = int(hours[best_hour_idx])
            confidence = float(round(probs[best_hour_idx], 2))
            hour_str = f"{best_hour:02d}:00"

            if confidence >= 0.55:
                recs.append(Recommendation(
                    rec_type='schedule',
                    priority=3,
                    title=f"Your predicted peak hour tomorrow: {hour_str}",
                    description=(
                        f"Based on your activity history, the model predicts you will be most "
                        f"productive at {hour_str} tomorrow "
                        f"(confidence: {confidence * 100:.0f}%). "
                        f"Schedule your most important task in that window."
                    ),
                    action_label='Update schedule',
                    icon='ti-clock',
                    confidence=confidence,
                    tags=['schedule', 'ml', 'productivity'],
                ))
        except Exception as exc:
            logger.warning("ML schedule recommender failed: %s", exc)

        return recs

    def _collaborative_recommendations(self) -> List[Recommendation]:
        """
        Peer-based recommendation using cosine similarity across skill vectors.
        Finds the most similar user and surfaces what they focus on that
        the current user neglects.
        """
        from apps.skills.models import UserSkill, SkillDomain
        from django.contrib.auth import get_user_model
        User = get_user_model()

        recs = []

        # Build skill score vectors for all users (anonymised)
        domains = SkillDomain.objects.filter(is_global=True).values_list('id', 'name')
        if not domains:
            return recs

        domain_ids = [d[0] for d in domains]
        domain_names = {d[0]: d[1] for d in domains}

        def user_vector(u):
            scores = {s.domain_id: s.current_score for s in UserSkill.objects.filter(user=u)}
            return np.array([scores.get(did, 0.0) for did in domain_ids])

        current_vec = user_vector(self.user).reshape(1, -1)

        # Sample other users (limit for performance)
        other_users = User.objects.exclude(id=self.user.id)[:50]
        if not other_users:
            return recs

        other_vecs = np.array([user_vector(u) for u in other_users])
        if other_vecs.shape[0] == 0 or np.all(current_vec == 0):
            return recs

        sims = cosine_similarity(current_vec, other_vecs)[0]
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])

        if best_sim < 0.3:
            return recs   # not similar enough to draw conclusions

        peer = other_users[best_idx]
        peer_vec = other_vecs[best_idx]
        diff = peer_vec - current_vec[0]

        # Find skill the peer excels at most that current user lags on
        neglected_idx = int(np.argmax(diff))
        neglected_domain_id = domain_ids[neglected_idx]
        neglected_name = domain_names.get(neglected_domain_id, 'this skill')
        gap = round(float(diff[neglected_idx]), 1)

        if gap >= 15:
            recs.append(Recommendation(
                rec_type='peer',
                priority=4,
                title=f"Peers like you invest more in {neglected_name}",
                description=(
                    f"Students with similar profiles score {gap:.0f} points higher in "
                    f"{neglected_name}. Dedicating 2–3 sessions per week could "
                    f"significantly boost your overall profile."
                ),
                action_label='Explore resources',
                icon='ti-users',
                confidence=round(best_sim, 2),
                tags=['peer', 'collaborative', neglected_name.lower()],
            ))

        return recs

    # ─── Post-processing ─────────────────────────────────────────────────────

    def _rank_and_filter(self, recs: List[Recommendation]) -> List[Recommendation]:
        """Sort by priority, remove duplicates, cap at MAX_RECS."""
        seen_types = set()
        unique = []
        for r in sorted(recs, key=lambda x: (x.priority, -x.confidence)):
            key = f"{r.rec_type}_{r.goal_id}_{r.skill_id}"
            if key not in seen_types:
                seen_types.add(key)
                unique.append(r)
        return unique[:MAX_RECS]

    def _save_recommendations(self, recs: List[Recommendation]):
        """Persist generated recommendations to the database."""
        from apps.recommendations.models import Recommendation as RecModel
        # Clear old unread recommendations
        RecModel.objects.filter(user=self.user, is_read=False).delete()
        for i, r in enumerate(recs, start=1):
            RecModel.objects.create(
                user=self.user,
                rec_type=r.rec_type,
                rank=i,
                title=r.title,
                description=r.description,
                action_label=r.action_label,
                goal_id=r.goal_id,
                skill_id=r.skill_id,
                icon=r.icon,
                confidence=r.confidence,
                tags=r.tags,
            )
