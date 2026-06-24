"""Celery application for GrowthPath async tasks."""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'growthpath.settings')

app = Celery('growthpath')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['growthpath'])
