# pedi_portal/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pedi_portal.settings.dev")

app = Celery("pedi_portal")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
