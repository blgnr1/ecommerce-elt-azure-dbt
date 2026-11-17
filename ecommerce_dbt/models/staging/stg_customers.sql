WITH kaynak AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_customers') }}
)

SELECT
    -- 1. Kimlik (ID) Alanı
    CAST(customer_id AS VARCHAR(50)) AS customer_id,

    -- 2. Demografik ve Kategorik Alanlar (Temizlenmiş ve standart isimlendirilmiş)
    TRIM(CAST(region AS VARCHAR(100))) AS customer_region,
    TRIM(CAST(customer_segment AS VARCHAR(50))) AS customer_segment,

    -- 3. Sayısal Müşteri Metrikleri
    CAST(age AS INT) AS customer_age,
    CAST(account_tenure_months AS INT) AS account_tenure_months

FROM kaynak