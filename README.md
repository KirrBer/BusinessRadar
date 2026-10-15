# BusinessRadar

## Запуск API

Требуются Docker и Docker Compose. При сборке контейнера обучаются модели из синтетических данных.

```sh
docker compose up --build
```

API доступен через Nginx на `http://localhost`: проверка состояния — `GET /health`, предсказание — `POST /api/v1/predict`. Для локальной разработки установите зависимости через `uv sync --group dev`, обучите модели командами `uv run python -m ml_core.train_rf` и `uv run python -m ml_core.train_kmeans`, затем запустите `uv run uvicorn app.main:app --reload`.

## Тесты

Для проверки нужны установленные зависимости и обученные модели:

```sh
uv sync --group dev
uv run python -m ml_core.train_rf
uv run python -m ml_core.train_kmeans
uv run pytest -q
```

GitHub Actions выполняет те же шаги при push и pull request.