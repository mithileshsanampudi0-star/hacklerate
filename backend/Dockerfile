FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects $PORT. Migrations run on every boot (no-op when up to date);
# demo data is loaded only when SEED_DEMO=true and the database is empty.
CMD alembic upgrade head \
    && if [ "$SEED_DEMO" = "true" ]; then python seed.py; fi \
    && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
