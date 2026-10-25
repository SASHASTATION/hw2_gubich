CREATE DATABASE IF NOT EXISTS transactions_db;
CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS transactions_db.transactions
(
    transaction_id String,
    transaction_time DateTime('UTC'),
    merch String,
    cat_id String,
    amount Float64,
    name_1 String,
    name_2 String,
    gender String,
    us_state String,
    lat Float64,
    lon Float64,
    merchant_lat Float64,
    merchant_lon Float64,
    target UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(transaction_time)
ORDER BY (us_state, transaction_time, transaction_id);
