# path/to/your/proj/src/cfehome/celery.py
import os
from celery import Celery
from decouple import config
from celery.schedules import crontab 

# set the default Django settings module for the 'celery' program.
# this is also used in manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_backend.settings')

app = Celery('core_backend')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clinic_emails_per_day': {
        'task': 'core_api.tasks.send_clinic_email',
        'schedule': crontab(hour='7,9,14,16', minute=0, day_of_week='1,2,3,4,5'),
    },
}
app.conf.timezone = 'US/Pacific'