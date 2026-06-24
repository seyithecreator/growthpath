"""apps/accounts/api_urls.py — Auth & user API routes"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.goals.api_views import CustomAuthToken, UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='api-users')

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='api-login'),
    path('', include(router.urls)),
]
