WITH islemler AS (
    SELECT * FROM {{ ref('stg_transaction') }}
),

-- Referans bütünlüğü kontrolü için dimension anahtarlarını alıyoruz
musteriler AS (
    SELECT customer_id FROM {{ ref('dim_customers') }}
),

saticilar AS (
    SELECT merchant_id FROM {{ ref('dim_merchants') }}
)

SELECT
    -- 1. Birincil ve Yabancı Anahtarlar (Star Schema Bağlantı Noktaları)
    t.transaction_id,
    t.customer_id,
    t.merchant_id,

    -- 2. Zaman Boyutu (Raporlarda günlük/saatlik gruplamayı hızlandırır)
    t.transaction_at,
    CAST(t.transaction_at AS DATE) AS transaction_date,
    DATEPART(HOUR, t.transaction_at) AS transaction_hour,

    -- 3. İşlem Bağlamı (O işleme özel nitelikler)
    t.payment_method,
    t.device_type,
    t.sales_channel,
    t.shipping_method,

    -- 4. Finansal Ölçümler (Measures)
    t.amount_usd AS gross_amount_usd,
    t.discount_percent,
    CAST(t.amount_usd * (1 - (t.discount_percent / 100.0)) AS DECIMAL(18, 2)) AS net_amount_usd,
    t.distance_from_billing_km,
    t.delivery_days,
    t.customer_satisfaction,

    -- 5. Risk ve Dolandırıcılık Sinyalleri
    t.failed_payment_attempts_24h,
    t.transactions_last_24h,
    t.previous_chargebacks,
    t.is_ip_mismatch,
    t.is_international,
    t.is_promotion_used,
    t.is_fraud,

    -- 6. İş Kuralı (Business Logic): İşlem Tutarı Segmenti
    CASE
        WHEN t.amount_usd >= 500 THEN 'Yuksek Tutar (500$+)'
        WHEN t.amount_usd >= 100 THEN 'Orta Tutar (100-499$)'
        ELSE 'Dusuk Tutar (<100$)'
    END AS amount_tier

FROM islemler t
INNER JOIN musteriler c ON t.customer_id = c.customer_id
INNER JOIN saticilar m ON t.merchant_id = m.merchant_id