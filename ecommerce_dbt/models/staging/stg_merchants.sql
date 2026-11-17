WITH kaynak AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_merchants') }}
)

SELECT
    -- 1. Kimlik (ID) Alanı
    CAST(merchant_id AS VARCHAR(50)) AS merchant_id,

    -- 2. Kategorik ve Coğrafi Alanlar (Boşluklardan arındırılmış ve standartlaştırılmış)
    TRIM(CAST(merchant_category AS VARCHAR(100))) AS merchant_category,
    TRIM(UPPER(CAST(merchant_country AS VARCHAR(50)))) AS merchant_country,

    -- 3. Risk Skoru (Hassas ondalık formatı)
    CAST(merchant_risk_score AS DECIMAL(6, 4)) AS merchant_risk_score

FROM kaynak