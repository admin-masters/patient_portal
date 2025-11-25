# analytics/tasks.py
from celery import shared_task
from django.core import management

@shared_task
def mask_patient_data_task():
    management.call_command("mask_patient_data")
