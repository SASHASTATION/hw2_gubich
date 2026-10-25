with merchant_metrics as (
    select
        merchant,
        count() as transaction_count,
        uniqExact(customer_id) as unique_customers,
        sum(is_fraud) as fraud_count,
        100.0 * sum(is_fraud) / count() as fraud_rate,
        sum(amount) as total_amount,
        sumIf(amount, is_fraud = 1) as fraud_amount,
        avg(amount) as avg_amount
    from {{ ref('stg_transactions') }}
    group by merchant
)

select
    *,
    fraud_rate >= 5 and transaction_count >= 20 as is_suspicious
from merchant_metrics
