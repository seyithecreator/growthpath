from django.urls import path
from . import views

app_name = 'priorities'

urlpatterns = [
    path('', views.priority_list, name='list'),
]
