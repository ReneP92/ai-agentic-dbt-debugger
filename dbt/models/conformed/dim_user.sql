WITH users AS (
    SELECT * FROM {{ ref('std_user') }}
)

SELECT
    user_id,
    username,
    email,
    first_name,
    last_name,
    date_of_birth,
    country_code,
    currency_code,
    status,
    kyc_level,
    registration_platform,
    registered_at,
    updated_at,

    -- Is the user fully KYC verified?
    CASE WHEN kyc_level = 'full' THEN TRUE ELSE FALSE END   AS is_kyc_verified,

    -- Is the account currently active?
    CASE WHEN status = 'active' THEN TRUE ELSE FALSE END     AS is_active,

    -- Registration device family
    CASE
        WHEN registration_platform IN ('ios', 'android') THEN 'mobile'
        WHEN registration_platform = 'web'               THEN 'desktop'
        ELSE 'unknown'
    END AS registration_device

FROM users
