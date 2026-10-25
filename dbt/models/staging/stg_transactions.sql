with normalized as (
    select
        transaction_id,
        toDateTime(transaction_time, 'UTC') as transaction_time,
        trimBoth(merch) as merchant,
        lower(trimBoth(cat_id)) as category,
        toDecimal64(toString(amount), 2) as amount,
        upper(trimBoth(name_1)) as first_name,
        upper(trimBoth(name_2)) as last_name,
        upper(trimBoth(gender)) as gender,
        upper(trimBoth(us_state)) as us_state,
        toFloat64(lat) as latitude,
        toFloat64(lon) as longitude,
        toFloat64(merchant_lat) as merchant_latitude,
        toFloat64(merchant_lon) as merchant_longitude,
        toUInt8(target) as is_fraud
    from {{ source('raw', 'transactions') }}
)

select
    transaction_id,
    transaction_time,
    toDate(transaction_time) as transaction_date,
    {{ dbt_date.day_of_week('transaction_time', isoweek=true) }} as day_of_week, -- noqa: LT05
    toHour(transaction_time) as transaction_hour,
    {{ dbt_utils.generate_surrogate_key([
        'first_name', 'last_name', 'gender', 'latitude', 'longitude'
    ]) }} as customer_id,
    merchant,
    category,
    amount,
    {{ amount_bucket('amount') }} as amount_bucket,
    gender,
    us_state,
    latitude,
    longitude,
    merchant_latitude,
    merchant_longitude,
    is_fraud
from normalized
