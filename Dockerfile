# Backend — Python 3.13 slim
FROM python:3.13-slim AS backend

WORKDIR /app

# System dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Alembic migrations then start uvicorn
CMD ["sh", "-c", "alembic upgrade head && python3 scripts/seed_data.py && python3 scripts/seed_colombia.py && uvicorn src.api.app:app --host 0.0.0.0 --port 8000"]
