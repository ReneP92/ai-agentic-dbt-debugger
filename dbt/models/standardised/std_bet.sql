-- Type casting and light normalisation only — no business logic, no joins.
SELECT
    CAST(id                     AS INTEGER)         AS bet_id,
    CAST(user_id                AS INTEGER)         AS user_id,
    CAST(LOWER(status)          AS VARCHAR)         AS status,
    CAST(LOWER(bet_type)        AS VARCHAR)         AS bet_type,
    CAST(sport                  AS VARCHAR)         AS sport,
    CAST(wager_amount           AS FLOAT)           AS wager_amount,
    CAST(potential_payout       AS FLOAT)           AS potential_payout,
    CAST(settled_amount         AS FLOAT)           AS settled_amount,
    CAST(LOWER(outcome)         AS VARCHAR)         AS outcome,
    CAST(odds                   AS FLOAT)           AS odds,
    CAST(UPPER(currency_code)   AS VARCHAR)         AS currency_code,
    CAST(placed_at              AS TIMESTAMP_NTZ)   AS placed_at,
    CAST(settled_at             AS TIMESTAMP_NTZ)   AS settled_at
FROM {{ source('raw', 'bets') }}
