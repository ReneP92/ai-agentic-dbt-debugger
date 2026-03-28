WITH bets AS (
    SELECT * FROM {{ ref('std_bet') }}
),

users AS (
    SELECT
        user_id,
        country_code,
        currency_code,
        is_kyc_verified,
        is_active
    FROM {{ ref('dim_user') }}
),

final AS (
    SELECT
        b.bet_id,
        b.user_id,
        u.country_code,
        u.is_kyc_verified,
        u.is_active             AS is_user_active,
        b.status,
        b.bet_type,
        b.sport,
        b.wager_amount,
        b.potential_payout,
        b.settled_amount,
        b.outcome,
        b.odds,
        b.currency_code,
        b.placed_at,
        b.settled_at,

        -- Gross gaming revenue from the house perspective:
        --   won  → house paid out more than it received (negative GGR)
        --   lost → house keeps the wager (positive GGR)
        --   void → no revenue
        --   open → unknown yet
        CASE
            WHEN b.outcome = 'lost' THEN b.wager_amount
            WHEN b.outcome = 'won'  THEN b.wager_amount - b.settled_amount
            WHEN b.outcome = 'void' THEN 0.0
            ELSE NULL
        END AS gross_gaming_revenue,

        -- Was the bet placed and settled on the same calendar day?
        CASE
            WHEN b.settled_at IS NOT NULL
             AND DATE(b.placed_at) = DATE(b.settled_at) THEN TRUE
            ELSE FALSE
        END AS is_same_day_settled

    FROM bets b
    LEFT JOIN users u ON u.user_id = b.user_id
)

SELECT * FROM final
