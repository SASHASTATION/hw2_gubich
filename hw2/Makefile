.PHONY: up sample run verify ps down
up:
	docker compose up --build -d
sample:
	DATA_DIR=./data CLICKHOUSE_HTTP_PORT=18123 docker compose -p mlops-hw2-smoke up -d
	DATA_DIR=./data CLICKHOUSE_HTTP_PORT=18123 docker compose -p mlops-hw2-smoke run --build --rm runner /data/sample.csv --output /results/smoke
run:
	docker compose run --build --rm runner /data/train.csv.gz /data/test.csv.gz
verify:
	docker compose run --build --rm runner /data/train.csv.gz /data/test.csv.gz --verify-only
ps:
	docker compose ps -a
down:
	docker compose down
