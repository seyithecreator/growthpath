"""apps/goals/api_urls.py — REST API routes"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    GoalViewSet, UserSkillViewSet, ActivityLogViewSet,
    PriorityViewSet, RecommendationViewSet,
)

router = DefaultRouter()
router.register(r'goals', GoalViewSet, basename='api-goals')
router.register(r'skills', UserSkillViewSet, basename='api-skills')
router.register(r'activities', ActivityLogViewSet, basename='api-activities')
router.register(r'priorities', PriorityViewSet, basename='api-priorities')
router.register(r'recommendations', RecommendationViewSet, basename='api-recommendations')

urlpatterns = [
    path('', include(router.urls)),
]
