# Kafka и ClickHouse

Проект загружает транзакции из CSV в Kafka, сохраняет их в ClickHouse и находит
**категорию самой крупной отдельной транзакции в каждом штате**.
Данные, SQL, результирующие CSV и Docker-окружение включены в репозиторий.

## Быстрый запуск

Нужны запущенный Docker и Docker Compose v2. Порт `8123` должен быть свободен.
Python и Git LFS на компьютере не нужны.

```bash
git clone https://github.com/SASHASTATION/hw2_gubich.git
cd hw2_gubich/hw2
docker compose up --build -d
docker compose run --build --rm runner /data/train.csv.gz /data/test.csv.gz
```

Скрипт прочитает gzip-архивы напрямую, отправит данные в Kafka, дождётся загрузки
в ClickHouse и сравнит оба SQL-запроса с независимым расчётом из CSV.
Успешный запуск заканчивается строкой `PASS: CSV -> Kafka -> ClickHouse; both SQL results match CSV reference`.

**Если данные уже загружены**, выполняйте проверку без повторной отправки:

```bash
docker compose run --rm runner /data/train.csv.gz /data/test.csv.gz --verify-only
```

## Результаты

Файлы сохраняются в `hw2/results/`:

- [Результирующий CSV](hw2/results/max_transaction_by_state_optimized.csv) — штат, категория и максимальная сумма.
- [CSV обычного запроса](hw2/results/max_transaction_by_state_baseline.csv) — тот же результат для сравнения.
- [Отчёт](hw2/results/report.json) — проверка, время запросов, прочитанные строки и размер таблиц.

На полном наборе проверены **1 048 575 транзакций**; получена **51 строка**:
50 штатов и округ Колумбия. Оба SQL совпали с расчётом через Python `Decimal`.
При равной сумме выбирается лексикографически наибольшая категория, затем ID.

| Вариант | Прочитано строк | Размер таблицы |
| --- | ---: | ---: |
| Исходное хранение | 1 048 575 | около 164 MB |
| Оптимизированное хранение | 1 048 575 | около 85 MB |
| Агрегированные максимумы | 51 | около 4,5 KB дополнительно |

В проверенном запуске предварительная агрегация ускорила запрос примерно в
**15 раз**, а основная таблица занимает примерно на **48% меньше места**.
Время зависит от машины; точные замеры — в отчёте.

## Как устроен проект

```text
CSV(.gz) → Python producer → Kafka → Kafka engine + materialized view
                                           ↓
                                    MergeTree: transactions
                                           ↓
                                    AggregatingMergeTree: state_max
```

| Файл | Назначение |
| --- | --- |
| `hw2/scripts/produce.py` | Потоковая отправка CSV/CSV.gz в Kafka с проверкой доставки |
| `hw2/scripts/run.py` | Загрузка, проверка результата и замеры |
| `hw2/sql/01_schema.sql` | DDL таблиц и materialized views |
| `hw2/sql/02_max_transaction_by_state.sql` | Обычный запрос с `argMax` |
| `hw2/sql/03_max_transaction_by_state_optimized.sql` | Быстрый запрос с `argMaxMerge` |
| `hw2/sql/00_baseline.sql` | Исходная таблица для сравнения хранения |
| `teta-ml-1-2025/` | Все три исходных CSV в gzip без потери данных |

Оптимизация: `LowCardinality` для повторяющихся строк, `ZSTD` и `Delta` для сжатия,
месячные партиции и сортировка по штату/времени. Основное ускорение запроса даёт
инкрементальное сохранение `argMaxState` в `AggregatingMergeTree`.
Все исходные поля сохраняются в `raw_json`; `sample_submition.csv.gz` содержит
шаблон ответа соревнования и в Kafka не загружается.

## Проверка и остановка

Следующие команды выполняются из папки `hw2`:

```bash
docker compose ps -a
docker compose logs --tail=30 init clickhouse kafka
docker compose down
```

Kafka и ClickHouse должны быть `healthy`, сервисы `init` и `kafka-init` — завершиться
с кодом `0`. Томá сохраняют данные после остановки: для возврата достаточно
`docker compose up -d`.

Повторная отправка CSV создаёт дубликаты, поэтому runner отказывается загружать
данные в непустую таблицу. Для полной перезагрузки **с удалением данных проекта**:

```bash
docker compose down -v
docker compose up -d
docker compose run --build --rm runner /data/train.csv.gz /data/test.csv.gz
```

Быстрый сквозной тест на 5 синтетических строках, включая равные максимумы:

```bash
make sample
# Повторная проверка этого теста:
DATA_DIR=./data CLICKHOUSE_HTTP_PORT=18123 docker compose -p mlops-hw2-smoke run --rm runner /data/sample.csv --output /results/smoke --verify-only
DATA_DIR=./data CLICKHOUSE_HTTP_PORT=18123 docker compose -p mlops-hw2-smoke down
```

Тест использует отдельные тома и порт `18123`; результаты — в `hw2/results/smoke/`.
Для собственных CSV задайте `DATA_DIR=/absolute/path/to/csv` перед командой
`docker compose run` и передайте имена файлов внутри `/data/`.

## ДЗ №4 — dbt и ClickHouse

Проект dbt находится в [`dbt/`](dbt/). Шесть аналитических витрин, тесты,
документация, скриншот DAG и команды запуска описаны в [HW4.md](HW4.md).
Исходный размеченный датасет используется из `teta-ml-1-2025/train.csv.gz`
без дополнительной копии ДЗ №2.
