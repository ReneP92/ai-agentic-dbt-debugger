-- Type casting and light normalisation only — no business logic, no joins.
SELECT
    CAST(id                     AS INTEGER)         AS transaction_id,
    CAST(user_id                AS INTEGER)         AS user_id,
    CAST(bet_id                 AS INTEGER)         AS bet_id,
    CAST(LOWER(type)            AS VARCHAR)         AS transaction_type,
    CAST(amount                 AS FLOAT)           AS amount,
    CAST(balance_after          AS FLOAT)           AS balance_after,
    CAST(UPPER(currency_code)   AS VARCHAR)         AS currency_code,
    CAST(processed_at           AS TIMESTAMP_NTZ)   AS processed_at,
    CAST(reference              AS VARCHAR)         AS reference
FROM {{ source('raw', 'transactions') }}
