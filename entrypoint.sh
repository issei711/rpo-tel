set -eu

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 8 \
    --timeout 60
