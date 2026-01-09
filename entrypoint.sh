set -eu

echo "entrypoint start"
echo "PORT=${PORT:-8080}"

# migrate（起動時に毎回。問題にならない）
python manage.py migrate --noinput

# ---- superuser 作成（フラグが立っている時だけ）----
if [ "${DJANGO_CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser --noinput || true
fi
# --------------------------------------------------

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 1 \
  --threads 2 \
  --timeout 0
