#!/usr/bin/env bash
python manage.py migrate
python manage.py collectstatic --no-input

(gunicorn core_backend.wsgi --user www-data --bind 0.0.0.0:8099 --workers 2) &
nginx -g "daemon off;"