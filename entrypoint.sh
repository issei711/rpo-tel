#!/bin/sh
set -eu

echo "entrypoint start"
echo "PORT=${PORT}"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 1 \
  --threads 2 \
  --timeout 0
