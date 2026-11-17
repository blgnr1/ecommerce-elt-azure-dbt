WITH kaynak AS (
    SELECT * FROM {{ source('ecommerce_raw', 'raw_transactions') }}
)

SELECT
    -- 1. Kimlik (ID) Alanları
    CAST(transaction_id AS VARCHAR(50)) AS transaction_id,
    CAST(customer_id AS VARCHAR(50)) AS customer_id,
    CAST(merchant_id AS VARCHAR(50)) AS merchant_id,

    -- 2. Tarih ve Zaman
    CAST(transaction_timestamp AS DATETIME2) AS transaction_at,

    -- 3. Kategorik Alanlar (Boşluklardan arındırılmış)
    TRIM(CAST(merchant_category AS VARCHAR(100))) AS merchant_category,
    TRIM(CAST(customer_region AS VARCHAR(100))) AS customer_region,
    TRIM(CAST(customer_segment AS VARCHAR(100))) AS customer_segment,
    TRIM(CAST(payment_method AS VARCHAR(50))) AS payment_method,
    TRIM(CAST(device_type AS VARCHAR(50))) AS device_type,
    TRIM(CAST(sales_channel AS VARCHAR(50))) AS sales_channel,
    TRIM(CAST(shipping_method AS VARCHAR(50))) AS shipping_method,

    -- 4. Finansal ve Ölçüm Alanları
    CAST(amount_usd AS DECIMAL(18, 2)) AS amount_usd,
    CAST(distance_from_billing_km AS DECIMAL(10, 2)) AS distance_from_billing_km,
    CAST(discount_percent AS DECIMAL(5, 2)) AS discount_percent,

    -- 5. Tam Sayı ve Puan Alanları
    CAST(customer_age AS INT) AS customer_age,
    CAST(account_tenure_months AS INT) AS account_tenure_months,
    CAST(failed_payment_attempts_24h AS INT) AS failed_payment_attempts_24h,
    CAST(transactions_last_24h AS INT) AS transactions_last_24h,
    CAST(previous_chargebacks AS INT) AS previous_chargebacks,
    CAST(delivery_days AS INT) AS delivery_days,
    CAST(customer_satisfaction AS DECIMAL(4, 2)) AS customer_satisfaction,

    -- 6. Evet/Hayır (0/1) Bayrakları
    CAST(ip_address_mismatch AS BIT) AS is_ip_mismatch,
    CAST(international_transaction AS BIT) AS is_international,
    CAST(promotion_used AS BIT) AS is_promotion_used,
    CAST(is_fraud AS BIT) AS is_fraud

FROM kaynak