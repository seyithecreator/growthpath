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
    path('generate-recommendations/', views.generate_recommendations, name='generate_recs'),
]
