FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY packages/quant-core/pyproject.toml packages/quant-core/pyproject.toml
COPY packages/quant-core/src packages/quant-core/src
COPY apps/server/pyproject.toml apps/server/pyproject.toml
COPY apps/server/src apps/server/src
COPY .env.example .env.example

RUN pip install -e packages/quant-core -e apps/server

EXPOSE 8000
CMD ["sh", "-c", "PYTHONPATH=/app/apps/server/src:/app/packages/quant-core/src uvicorn limitboard_server.main:app --host 0.0.0.0 --port ${SERVER_PORT:-8000}"]
