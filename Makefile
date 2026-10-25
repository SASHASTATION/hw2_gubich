PYTHON ?= python
DBT = cd dbt && dbt
DATA ?= teta-ml-1-2025/train.csv.gz

.PHONY: install up load deps seed run test build docs serve lint fix verify validate down
install:
	$(PYTHON) -m pip install -r requirements.txt
up:
	docker compose up -d --wait
load:
	$(PYTHON) scripts/load_transactions.py "$(DATA)"
deps:
	$(DBT) deps --profiles-dir .
seed:
	$(DBT) seed --profiles-dir .
run:
	$(DBT) run --profiles-dir .
test:
	$(DBT) test --profiles-dir .
build:
	$(DBT) build --profiles-dir .
docs:
	$(DBT) docs generate --profiles-dir .
serve:
	$(DBT) docs serve --profiles-dir . --host 127.0.0.1 --port 8084
lint:
	bash scripts/lint.sh
fix:
	cd dbt && sqlfluff fix models tests
verify:
	$(PYTHON) scripts/verify_results.py "$(DATA)"
validate:
	$(PYTHON) scripts/validate.py "$(DATA)"
down:
	docker compose down
