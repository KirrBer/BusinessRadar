# BusinessRadar

## Запуск приложения

Требуются Docker и Docker Compose. При сборке backend-контейнера обучаются модели из синтетических данных. Next.js обслуживает интерфейс, Nginx направляет `/api` в FastAPI.

```sh
docker compose up --build
```

Интерфейс доступен на `http://localhost`. Проверка состояния API — `GET /health`, предсказание — `POST /api/v1/predict`.

Для локальной разработки запустите backend в первом терминале:

```sh
uv sync --group dev --no-install-project
uv run --no-sync python -m ml_core.train_rf
uv run --no-sync python -m ml_core.train_kmeans
uv run --no-sync uvicorn app.main:app --reload --port 8000
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
| `pop_density` | Синтетический индекс плотности района, не официальная статистика |
| `competitors` | Условное число конкурентов в зоне анализа |
| `avg_check` | Средний чек в рублях |
| `peak_factor` | Доля пикового спроса от 0 до 1 |
| `income_area` | Индекс дохода относительно среднего: `1.0` — средний |
| `rent_cost` | Нормализованный индекс аренды от 0 до 1, не рубли за м² |

Карта показывает реальные границы 18 районов Санкт-Петербурга из OpenStreetMap.
Атрибуция и условия ODbL указаны под картой и в локальном GeoJSON. Для обновления
границ используйте `uv run --no-project --with shapely python -m scripts.fetch_spb_boundaries`.

Сервис работает на синтетических данных, сгенерированных внутри полигонов этих
районов. Поэтому трафик, плотность, конкуренты, доход и аренда — модельные оценки;
они не подтягиваются автоматически из карт или банковских транзакций.

## Тесты

Для проверки нужны установленные зависимости и обученные модели:

```sh
uv sync --group dev --no-install-project
uv run --no-sync python -m ml_core.train_rf
uv run --no-sync python -m ml_core.train_kmeans
uv run --no-sync pytest -q
```

GitHub Actions запускает ML-тесты, ESLint и production build Next.js при push и pull request.