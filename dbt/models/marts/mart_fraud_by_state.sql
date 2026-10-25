select
    t.us_state,
    s.state_name,
    count() as transaction_count,
    sum(t.is_fraud) as fraud_count,
    100.0 * sum(t.is_fraud) / count() as fraud_rate,
    uniqExact(t.customer_id) as unique_customers,
    uniqExact(t.merchant) as unique_merchants,
    sum(t.amount) as total_amount,
    sumIf(t.amount, t.is_fraud = 1) as fraud_amount
from {{ ref('stg_transactions') }} as t
left join {{ ref('states') }} as s on t.us_state = s.us_state
group by t.us_state, s.state_name
