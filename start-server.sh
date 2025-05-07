#!/usr/bin/env bash
python manage.py migrate
python manage.py collectstatic --no-input

(gunicorn core_backend.wsgi --user www-data --bind 0.0.0.0:8099 --workers 2) &
nginx -g "daemon off;"

celery -A core_backend worker -E -l info
celery -A core_backend beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler