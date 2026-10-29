# BusinessRadar

## Запуск приложения

Требуются Docker и Docker Compose, а также реальный датасет в CSV. При старте backend обучает RF/KMeans по этому датасету. Compose монтирует `BUSINESSRADAR_HOST_DATA_DIR` (по умолчанию `./data`) в `/app/data`; без обязательных CSV backend завершится с ошибкой. Next.js обслуживает интерфейс, Nginx направляет `/api` в FastAPI.

```powershell
$env:BUSINESSRADAR_HOST_DATA_DIR = "C:\data\businessradar"
docker compose up --build
```

Синтетическое демо доступно только по явному переключателю:

```powershell
$env:BUSINESSRADAR_DEMO = "true"
docker compose up --build
```

Интерфейс доступен на `http://localhost`. Проверка состояния API — `GET /health`, предсказание — `POST /api/v1/predict`.

Для локальной разработки укажите каталог реальных CSV и запустите backend в первом терминале:

```powershell
uv sync --group dev --no-install-project
$env:BUSINESSRADAR_DATA_DIR = "C:\data\businessradar"
uv run --no-sync python -m ml_core.startup
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
| `traffic` | Показатель трафика из источника выгрузки; единицы должны совпадать в обучении и запросе |
| `pop_density` | Плотность населения из источника выгрузки, обычно жителей на км² |
| `competitors` | Число конкурентов из источника выгрузки |
| `avg_check` | Средний чек в рублях |
| `peak_factor` | Доля пикового спроса от 0 до 1 |
| `income_area` | Индекс дохода из выгрузки: `1.0` — средний уровень |
| `rent_cost` | Нормализованный индекс аренды от 0 до 1, не рубли за м² |

Обучение по умолчанию требует реальные выгрузки из каталога `BUSINESSRADAR_DATA_DIR`
(по умолчанию `data`). Синтетический режим является только явным demo-режимом:
`BUSINESSRADAR_DEMO=true` либо `uv run python -m ml_core.train_rf --demo`.

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

Поля для обучающего target берутся из реальных обезличенных транзакций: без них
реальный прогноз спроса невозможен. Интеграции с 2GIS, Яндексом, ЦИАН и DWH
в `ml_core/adapters` пока являются заглушками/fallback-профилями и не считаются
реальными источниками. Подготовьте CSV-выгрузки вручную или подключите официальные
доступы перед использованием в production. Обучение реальными данными:

```powershell
$env:BUSINESSRADAR_DATA_DIR = "C:\data\businessradar"
uv run --no-sync python -m ml_core.train_rf
uv run --no-sync python -m ml_core.train_kmeans
```

Карта показывает реальные границы 18 районов Санкт-Петербурга из OpenStreetMap.
Атрибуция и условия ODbL указаны под картой и в локальном GeoJSON. Для обновления
границ используйте `uv run --no-project --with shapely python -m scripts.fetch_spb_boundaries`.

При запуске в demo-режиме сервис использует синтетические данные, сгенерированные
внутри полигонов этих районов. В этом режиме трафик, плотность, конкуренты, доход
и аренда — модельные оценки; они не подтягиваются автоматически из карт или
банковских транзакций.

## Тесты

Для проверки нужны установленные зависимости и обученные модели:

```sh
uv sync --group dev --no-install-project
uv run --no-sync python -m ml_core.train_rf --demo
uv run --no-sync python -m ml_core.train_kmeans --demo
uv run --no-sync pytest -q
```

GitHub Actions запускает ML-тесты, ESLint и production build Next.js при push и pull request.