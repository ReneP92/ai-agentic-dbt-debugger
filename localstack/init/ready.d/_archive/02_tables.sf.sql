-- 02_tables.sf.sql
-- Creates raw source tables in the RAW schema.
-- These mirror what a loader (Fivetran, Airbyte, etc.) would land in production.

USE DATABASE BETTING;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS USERS (
    id                      INTEGER         NOT NULL,
    username                VARCHAR(100)    NOT NULL,
    email                   VARCHAR(255)    NOT NULL,
    first_name              VARCHAR(100),
    last_name               VARCHAR(100),
    date_of_birth           DATE,
    country_code            VARCHAR(3),
    currency_code           VARCHAR(3)      NOT NULL DEFAULT 'GBP',
    status                  VARCHAR(50)     NOT NULL DEFAULT 'active',  -- active | suspended
    kyc_level               VARCHAR(50)     NOT NULL DEFAULT 'none',    -- none | partial | full
    registration_platform   VARCHAR(50),                                -- web | ios | android
    created_at              TIMESTAMP_NTZ   NOT NULL,
    updated_at              TIMESTAMP_NTZ   NOT NULL
);

CREATE TABLE IF NOT EXISTS BETS (
    id                  INTEGER         NOT NULL,
    user_id             INTEGER         NOT NULL,
    status              VARCHAR(50)     NOT NULL,   -- open | settled | void
    bet_type            VARCHAR(50)     NOT NULL,   -- single | accumulator
    sport               VARCHAR(100),
    wager_amount        FLOAT           NOT NULL,
    potential_payout    FLOAT,
    settled_amount      FLOAT,
    outcome             VARCHAR(50),                -- won | lost | void | NULL (open)
    odds                FLOAT           NOT NULL,
    currency_code       VARCHAR(3)      NOT NULL DEFAULT 'GBP',
    placed_at           TIMESTAMP_NTZ   NOT NULL,
    settled_at          TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS TRANSACTIONS (
    id              INTEGER         NOT NULL,
    user_id         INTEGER         NOT NULL,
    bet_id          INTEGER,                        -- NULL for deposits / withdrawals
    type            VARCHAR(100)    NOT NULL,       -- deposit | withdrawal | bet | winnings | refund
    amount          FLOAT           NOT NULL,       -- positive = credit, negative = debit
    balance_after   FLOAT           NOT NULL,
    currency_code   VARCHAR(3)      NOT NULL DEFAULT 'GBP',
    processed_at    TIMESTAMP_NTZ   NOT NULL,
    reference       VARCHAR(255)
);
