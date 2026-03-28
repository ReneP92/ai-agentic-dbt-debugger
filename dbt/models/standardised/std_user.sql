-- Type casting and light normalisation only — no business logic, no joins.
SELECT
    CAST(id                     AS INTEGER)         AS user_id,
    CAST(username               AS VARCHAR)         AS username,
    CAST(LOWER(email)           AS VARCHAR)         AS email,
    CAST(first_name             AS VARCHAR)         AS first_name,
    CAST(last_name              AS VARCHAR)         AS last_name,
    CAST(date_of_birth          AS DATE)            AS date_of_birth,
    CAST(UPPER(country_code)    AS VARCHAR)         AS country_code,
    CAST(UPPER(currency_code)   AS VARCHAR)         AS currency_code,
    CAST(LOWER(status)          AS VARCHAR)         AS status,
    CAST(LOWER(kyc_level)       AS VARCHAR)         AS kyc_level,
    CAST(LOWER(registration_platform) AS VARCHAR)   AS registration_platform,
    CAST(created_at             AS TIMESTAMP_NTZ)   AS registered_at,
    CAST(updated_at             AS TIMESTAMP_NTZ)   AS updated_at
FROM {{ source('raw', 'users') }}
