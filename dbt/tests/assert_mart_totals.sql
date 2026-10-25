{% for model in [
    'mart_daily_state_metrics', 'mart_fraud_by_category', 'mart_fraud_by_state',
    'mart_customer_risk_profile', 'mart_hourly_fraud_pattern', 'mart_merchant_analytics'
] %}
    select '{{ model }}' as model_name
    from {{ ref(model) }} as m
    having
        sum(m.transaction_count) != (select count() from {{ ref('stg_transactions') }})
        or sum(m.total_amount) != (select sum(s.amount) from {{ ref('stg_transactions') }} as s)
    {% if not loop.last %}union all{% endif %}
{% endfor %}
