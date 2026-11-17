WITH saticilar AS (
    SELECT * FROM {{ ref('stg_merchants') }}
)

SELECT
    merchant_id,
    merchant_category,
    merchant_country,
    merchant_risk_score,

    -- İş Kuralı (Business Logic): Satıcı Risk Seviyesi
    CASE
        WHEN merchant_risk_score >= 0.70 THEN 'Yuksek Risk'
        WHEN merchant_risk_score >= 0.30 THEN 'Orta Risk'
        ELSE 'Dusuk Risk'
    END AS merchant_risk_tier

FROM saticilar