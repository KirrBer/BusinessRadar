FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN python -m pip install --no-cache-dir uv==0.8.15
RUN uv sync --no-dev --no-install-project

COPY ml_core ./ml_core
COPY app ./app
COPY scripts ./scripts
ENV BUSINESSRADAR_DATA_DIR=/app/data

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "python", "-m", "ml_core.startup"]