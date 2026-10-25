{# dbt_date 0.10.1 has no native ClickHouse dispatch for this macro. #}
{% macro clickhouse__day_of_week(date, isoweek) -%}
    {% if isoweek %}
        toDayOfWeek({{ date }})
    {% else %}
        modulo(toDayOfWeek({{ date }}), 7) + 1
    {% endif %}
{%- endmacro %}
