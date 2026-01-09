FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 先に entrypoint だけコピーして確実に整形する
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# 残りをコピー
COPY . /app

# sh 経由で起動（exec format error を潰す）
CMD ["sh", "/app/entrypoint.sh"]
