"""apps/goals/urls.py"""

from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alias'),
    path('list/', views.goal_list, name='list'),
    path('create/', views.goal_create, name='create'),
    path('<int:pk>/', views.goal_detail, name='detail'),
    path('<int:pk>/edit/', views.goal_update, name='update'),
    path('<int:pk>/progress/', views.goal_update_progress, name='update_progress'),
    path('<int:pk>/log-activity/', views.goal_log_activity, name='log_activity'),
    path('<int:pk>/generate-roadmap/', views.generate_roadmap, name='generate_roadmap'),
    path('<int:goal_pk>/milestone/<int:milestone_pk>/complete/', views.complete_milestone, name='complete_milestone'),
    path('generate-recommendations/', views.generate_recommendations, name='generate_recs'),
]
