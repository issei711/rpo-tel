FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY . /app

# collectstatic が prod 設定（manifest）で走るようにする
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
# ビルド時に SECRET_KEY 未設定で落ちるのを防ぐ（本番はCloud Runの環境変数が使われる）
ENV DJANGO_SECRET_KEY=dummy-for-build

RUN python manage.py collectstatic --noinput

CMD ["sh", "/app/entrypoint.sh"]
