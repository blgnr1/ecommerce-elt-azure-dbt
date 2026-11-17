WITH musteriler AS (
    SELECT * FROM {{ ref('stg_customers') }}
)

SELECT
    customer_id,
    customer_region,
    customer_segment,
    customer_age,
    account_tenure_months,

    -- İş Kuralı (Business Logic): Müşteri Sadakat / Kıdem Grubu
    CASE
        WHEN account_tenure_months >= 36 THEN 'Sadik Musteri (3+ Yil)'
        WHEN account_tenure_months >= 12 THEN 'Gelisen Musteri (1-3 Yil)'
        ELSE 'Yeni Musteri (0-1 Yil)'
    END AS tenure_group

FROM musteriler