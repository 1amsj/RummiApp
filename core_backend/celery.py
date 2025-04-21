# path/to/your/proj/src/cfehome/celery.py
import os
from celery import Celery
from decouple import config

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

#app.conf.beat_schedule = {
#    'add-every-30-seconds': {
#        'task': 'tasks.send_print_tasked',
#        'schedule': 30.0,
#        'args': (16, 16)
#    },
#}
#app.conf.timezone = 'UTC'

# We used CELERY_BROKER_URL in settings.py instead of:
# app.conf.broker_url = ''

# We used CELERY_BEAT_SCHEDULER in settings.py instead of:
# app.conf.beat_scheduler = ''django_celery_beat.schedulers.DatabaseScheduler'