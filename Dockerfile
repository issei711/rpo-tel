FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# WhiteNoise運用なら collectstatic はビルド時にやるのが綺麗
# ※ SECRET_KEY が必要な設定を書いてる場合は、prod.py 側で collectstatic を阻害しない設計にする
RUN python manage.py collectstatic --noinput

RUN chmod +x /app/entrypoint.sh

CMD ["sh", "/app/entrypoint.sh"]
