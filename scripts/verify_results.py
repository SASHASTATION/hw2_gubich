"""Independent CSV/Decimal reference for all six mart partitions."""
import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from load_transactions import client, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    reference = defaultdict(lambda: [0, Decimal(0), 0])
    for row in rows(args.csv):
        key = row['cat_id'].strip().lower()
        reference[key][0] += 1
        reference[key][1] += Decimal(row['amount'])
        reference[key][2] += int(row['target'])
    db = client()
    schema = os.getenv('CLICKHOUSE_SCHEMA', 'analytics')
    import re
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', schema):
        raise ValueError('Invalid schema identifier')
    actual = db.query(f'SELECT category, transaction_count, total_amount, fraud_count '
                      f'FROM {schema}.mart_fraud_by_category').result_rows
    result = {r[0]: list(r[1:]) for r in actual}
    if result != dict(reference):
        raise AssertionError('Category aggregates differ from CSV reference')
    expected = [sum(v[i] for v in reference.values()) for i in range(3)]
    models = ['mart_daily_state_metrics', 'mart_fraud_by_category', 'mart_fraud_by_state',
              'mart_customer_risk_profile', 'mart_hourly_fraud_pattern', 'mart_merchant_analytics']
    report = {'source': args.csv.name, 'transactions': expected[0],
              'total_amount': str(expected[1]), 'frauds': expected[2], 'marts': {}}
    for model in models:
        fields = 'sum(transaction_count), sum(total_amount)'
        if model != 'mart_daily_state_metrics':
            fields += ', sum(fraud_count)'
        values = list(db.query(f'SELECT {fields} FROM {schema}.{model}').first_row)
        if values != expected[:len(values)]:
            raise AssertionError(f'{model}: {values} != {expected}')
        report['marts'][model] = {'rows': int(db.command(f'SELECT count() FROM {schema}.{model}')),
                                'totals_match_csv': True}
    path = Path(__file__).resolve().parents[1] / 'artifacts' / 'verification.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    import os
    main()
