#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../dbt"
sqlfluff lint models tests
