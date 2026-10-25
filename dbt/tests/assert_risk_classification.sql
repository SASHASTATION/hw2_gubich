select customer_id
from {{ ref('mart_customer_risk_profile') }}
where
    (fraud_rate >= 5 and risk_level != 'HIGH')
    or (fraud_rate >= 1 and fraud_rate < 5 and risk_level != 'MEDIUM')
    or (fraud_rate < 1 and risk_level != 'LOW')
