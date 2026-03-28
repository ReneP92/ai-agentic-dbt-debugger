{{
    config(materialized='table')
}}

SELECT
    DATE(placed_at)                                         AS bet_date,
    sport,
    bet_type,
    currency_code,
    country_code,

    COUNT(*)                                                AS total_bets,
    COUNT(CASE WHEN status = 'settled' THEN 1 END)          AS settled_bets,
    COUNT(CASE WHEN status = 'open'    THEN 1 END)          AS open_bets,
    COUNT(CASE WHEN outcome = 'won'    THEN 1 END)          AS winning_bets,
    COUNT(CASE WHEN outcome = 'lost'   THEN 1 END)          AS losing_bets,

    SUM(wager_amount)                                       AS total_wager,
    SUM(settled_amount)                                     AS total_settled_amount,
    SUM(gross_gaming_revenue)                               AS total_ggr,

    AVG(odds)                                               AS avg_odds,
    COUNT(DISTINCT user_id)                                 AS unique_bettors

FROM {{ ref('fct_bet') }}
GROUP BY 1, 2, 3, 4, 5
