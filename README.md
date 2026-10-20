# BusinessRadar

## Запуск приложения

Требуются Docker и Docker Compose. При сборке backend-контейнера обучаются модели из синтетических данных. Next.js обслуживает интерфейс, Nginx направляет `/api` в FastAPI.

```sh
docker compose up --build
```

Интерфейс доступен на `http://localhost`. Проверка состояния API — `GET /health`, предсказание — `POST /api/v1/predict`.

Для локальной разработки запустите backend в первом терминале:

```sh
uv sync --group dev
uv run python -m ml_core.train_rf
uv run python -m ml_core.train_kmeans
uv run uvicorn app.main:app --reload --port 8000
```

Во втором терминале запустите Next.js:

```sh
cd frontend
npm ci
npm run dev
```

Страница откроется на `http://localhost:3000`; Next.js перенаправляет API-запросы на локальный backend.

### Единицы признаков

Форма принимает следующие значения:

| Признак | Единица и смысл |
| --- | --- |
| `lat`, `lon` | Географические координаты в градусах |
| `traffic` | Условная оценка потенциальных посетителей в день |
| `pop_density` | Жители на км² |
| `competitors` | Условное число конкурентов в зоне анализа |
| `avg_check` | Средний чек в рублях |
| `peak_factor` | Доля пикового спроса от 0 до 1 |
| `income_area` | Индекс дохода относительно среднего: `1.0` — средний |
| `rent_cost` | Нормализованный индекс аренды от 0 до 1, не рубли за м² |

Обучение по умолчанию использует реальные выгрузки из каталога
`BUSINESSRADAR_DATA_DIR` (по умолчанию `data`). Синтетический режим теперь
является только явным demo-режимом: `uv run python -m ml_core.train_rf --demo`.

### Схема выгрузок

ETL в `ml_core/data_pipeline.py` объединяет данные по `location_id`:

* `addresses.csv`: `location_id`, `lat`, `lon` (справочник адресов);
* `area_metrics.csv`: `location_id`, `traffic`, `pop_density` и, опционально,
  `competitors`, `income_area`, `rent_cost`;
* `competitors.csv`: `location_id`, `competitors` (если конкуренты пришли
  отдельной выгрузкой);
* `property_metrics.csv`: `location_id`, `rent_per_sqm`, `income_area`
  (данные баз недвижимости и банка; `rent_cost` нормализуется по выгрузке);
* `transactions.csv`: `location_id`, `amount`, `transaction_at` (агрегаты
  эквайринга: `avg_check`, дневной `demand` и `peak_factor` считаются в ETL).

Таким образом, адаптеры 2GIS/Росстата, парсер Яндекс.Карт и выгрузки ЦИАН/
Авито должны только записать эти колонки. Обучение реальными данными:

```sh
$env:BUSINESSRADAR_DATA_DIR = "C:\data\businessradar"
uv run python -m ml_core.train_rf
uv run python -m ml_core.train_kmeans
```

## Тесты

Для проверки нужны установленные зависимости и обученные модели:

```sh
uv sync --group dev
uv run python -m ml_core.train_rf
uv run python -m ml_core.train_kmeans
uv run pytest -q
```

GitHub Actions запускает ML-тесты, ESLint и production build Next.js при push и pull request.