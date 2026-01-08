set -eu

echo "entrypoint start"
echo "PORT=$PORT"

# 静的ファイル（必要なら）
python manage.py collectstatic --noinput || true

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 2 \
  --threads 4 \
  --timeout 0
