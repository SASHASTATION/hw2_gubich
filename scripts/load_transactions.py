"""Load the labeled HW2 CSV without inventing targets for the competition test set."""
import argparse
import csv
import gzip
import hashlib
import os
from datetime import datetime
from pathlib import Path

import clickhouse_connect


def client():
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.getenv('CLICKHOUSE_PORT', '18124')),
        username=os.getenv('CLICKHOUSE_USER', 'dbt'),
        password=os.getenv('CLICKHOUSE_PASSWORD', 'dbt_local'),
    )


def rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        required = {'target', 'transaction_time', 'merch', 'cat_id', 'amount',
                    'name_1', 'name_2', 'gender', 'us_state', 'lat', 'lon',
                    'merchant_lat', 'merchant_lon'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing columns: {sorted(missing)}. Use labeled train.csv.gz.')
        yield from reader


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    # Validate the file before touching the database.
    source = rows(args.csv)
    first = next(source, None)
    if first is None:
        raise ValueError('Source CSV is empty')
    db = client()
    existing = db.command('SELECT count() FROM transactions_db.transactions')
    if int(existing):
        raise RuntimeError(f'Table already contains {existing} rows; skipping unsafe duplicate load.')
    columns = ['transaction_id', 'transaction_time', 'merch', 'cat_id', 'amount',
               'name_1', 'name_2', 'gender', 'us_state', 'lat', 'lon',
               'merchant_lat', 'merchant_lon', 'target']
    import itertools
    batch = []
    count = 0
    for number, row in enumerate(itertools.chain([first], source), 1):
        label = int(row['target'])
        if label not in (0, 1):
            raise ValueError(f'Invalid target at row {number}')
        # File row number preserves separate identical events; the filename is not part of identity.
        identity = f'{number}:' + ':'.join(row[key] for key in sorted(row))
        batch.append([
            hashlib.sha256(identity.encode()).hexdigest(),
            datetime.fromisoformat(row['transaction_time']), row['merch'], row['cat_id'],
            float(row['amount']), row['name_1'], row['name_2'], row['gender'], row['us_state'],
            *[float(row[key]) for key in ['lat', 'lon', 'merchant_lat', 'merchant_lon']], label,
        ])
        if len(batch) == 10000:
            db.insert('transactions_db.transactions', batch, column_names=columns)
            count += len(batch)
            batch.clear()
    if batch:
        db.insert('transactions_db.transactions', batch, column_names=columns)
        count += len(batch)
    actual = int(db.command('SELECT count() FROM transactions_db.transactions'))
    if actual != count:
        raise RuntimeError(f'Loaded {actual}, expected {count}')
    print(f'Loaded {count} labeled transactions from {args.csv.name}')


if __name__ == '__main__':
    main()
