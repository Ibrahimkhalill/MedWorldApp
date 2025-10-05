import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medworld.settings')

app = Celery('medworld')

# Load task settings from Django settings file
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks.py files in all Django apps
app.autodiscover_tasks()
