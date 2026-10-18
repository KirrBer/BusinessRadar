FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN python -m pip install --no-cache-dir uv==0.8.15
RUN uv sync --no-dev --no-install-project

COPY ml_core ./ml_core
COPY app ./app
RUN uv run --no-sync python -m ml_core.train_rf \
    && uv run --no-sync python -m ml_core.train_kmeans

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]