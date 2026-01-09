#!/bin/sh
set -eu

echo "entrypoint start"
echo "PORT=${PORT:-8080}"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 1 \
  --threads 2 \
  --timeout 0
