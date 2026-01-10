#!/bin/sh
set -eu

echo "entrypoint start"
echo "PORT=${PORT}"
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-}"
echo "PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-}"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 1 \
  --threads 2 \
  --timeout 0 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --log-level debug
