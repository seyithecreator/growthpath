"""GrowthPath – Root URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.goals import views as goal_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Redirect root to dashboard
    path('', goal_views.dashboard),

    # Auth views (login, logout)
    path('accounts/', include('apps.accounts.urls')),

    # Main application pages
    path('goals/', include('apps.goals.urls', namespace='goals')),
    path('skills/', include('apps.skills.urls', namespace='skills')),
    path('activities/', include('apps.activities.urls', namespace='activities')),
    path('priorities/', include('apps.priorities.urls', namespace='priorities')),
    path('recommendations/', include('apps.recommendations.urls', namespace='recommendations')),

    # REST API — auth at /api/v1/auth/, all resources at /api/v1/<resource>/
    path('api/v1/', include([
        path('auth/', include('apps.accounts.api_urls')),
        path('', include('apps.goals.api_urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
