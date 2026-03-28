"""
01_seed.py
Initialises the BETTING database with schemas, tables, and seed data.
Executed as a LocalStack ready.d init hook (Python scripts are natively supported).
Replaces the .sf.sql files which fail to CREATE DATABASE on the LocalStack Snowflake emulator.
"""

import snowflake.connector

CONN_PARAMS = dict(
    host="snowflake.localhost.localstack.cloud",
    port=4566,
    account="localstack",
    user="test",
    password="test",
    protocol="https",
)

SETUP_SQL = [
    "CREATE DATABASE IF NOT EXISTS BETTING",
    "CREATE WAREHOUSE IF NOT EXISTS TRANSFORM WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE",
    "USE DATABASE BETTING",
    "CREATE SCHEMA IF NOT EXISTS RAW",
    "CREATE SCHEMA IF NOT EXISTS STANDARDISED",
    "CREATE SCHEMA IF NOT EXISTS CONFORMED",
    "CREATE SCHEMA IF NOT EXISTS MART",
]

TABLE_SQL = [
    "USE DATABASE BETTING",
    "USE SCHEMA RAW",
    """CREATE TABLE IF NOT EXISTS USERS (
        id                      INTEGER         NOT NULL,
        username                VARCHAR(100)    NOT NULL,
        email                   VARCHAR(255)    NOT NULL,
        first_name              VARCHAR(100),
        last_name               VARCHAR(100),
        date_of_birth           DATE,
        country_code            VARCHAR(3),
        currency_code           VARCHAR(3)      NOT NULL DEFAULT 'GBP',
        status                  VARCHAR(50)     NOT NULL DEFAULT 'active',
        kyc_level               VARCHAR(50)     NOT NULL DEFAULT 'none',
        registration_platform   VARCHAR(50),
        created_at              TIMESTAMP_NTZ   NOT NULL,
        updated_at              TIMESTAMP_NTZ   NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS BETS (
        id                  INTEGER         NOT NULL,
        user_id             INTEGER         NOT NULL,
        status              VARCHAR(50)     NOT NULL,
        bet_type            VARCHAR(50)     NOT NULL,
        sport               VARCHAR(100),
        wager_amount        FLOAT           NOT NULL,
        potential_payout    FLOAT,
        settled_amount      FLOAT,
        outcome             VARCHAR(50),
        odds                FLOAT           NOT NULL,
        currency_code       VARCHAR(3)      NOT NULL DEFAULT 'GBP',
        placed_at           TIMESTAMP_NTZ   NOT NULL,
        settled_at          TIMESTAMP_NTZ
    )""",
    """CREATE TABLE IF NOT EXISTS TRANSACTIONS (
        id              INTEGER         NOT NULL,
        user_id         INTEGER         NOT NULL,
        bet_id          INTEGER,
        type            VARCHAR(100)    NOT NULL,
        amount          FLOAT           NOT NULL,
        balance_after   FLOAT           NOT NULL,
        currency_code   VARCHAR(3)      NOT NULL DEFAULT 'GBP',
        processed_at    TIMESTAMP_NTZ   NOT NULL,
        reference       VARCHAR(255)
    )""",
]

SEED_SQL = [
    "USE DATABASE BETTING",
    "USE SCHEMA RAW",
    """INSERT INTO USERS (id, username, email, first_name, last_name, date_of_birth, country_code, currency_code, status, kyc_level, registration_platform, created_at, updated_at) VALUES
      (1,  'jsmith',    'j.smith@example.com',    'John',    'Smith',    '1988-03-15', 'GB', 'GBP', 'active',    'full',    'web',     '2023-01-10 09:00:00', '2023-01-10 09:00:00'),
      (2,  'emiller',   'e.miller@example.com',   'Emma',    'Miller',   '1992-07-22', 'GB', 'GBP', 'active',    'full',    'ios',     '2023-02-14 11:30:00', '2023-03-01 08:00:00'),
      (3,  'rbrown',    'r.brown@example.com',    'Robert',  'Brown',    '1985-11-05', 'GB', 'GBP', 'suspended', 'partial', 'web',     '2023-01-20 14:00:00', '2023-04-10 16:00:00'),
      (4,  'lwilson',   'l.wilson@example.com',   'Laura',   'Wilson',   '1995-04-18', 'GB', 'GBP', 'active',    'full',    'android', '2023-03-05 10:00:00', '2023-03-05 10:00:00'),
      (5,  'dtaylor',   'd.taylor@example.com',   'David',   'Taylor',   '1990-09-30', 'GB', 'GBP', 'active',    'none',    'web',     '2023-04-01 08:30:00', '2023-04-01 08:30:00'),
      (6,  'mjohnson',  'm.johnson@example.com',  'Michael', 'Johnson',  '1987-06-12', 'US', 'USD', 'active',    'full',    'ios',     '2023-01-15 15:00:00', '2023-01-15 15:00:00'),
      (7,  'swhite',    's.white@example.com',    'Sarah',   'White',    '1993-02-28', 'US', 'USD', 'active',    'full',    'web',     '2023-02-20 09:45:00', '2023-02-20 09:45:00'),
      (8,  'cmartin',   'c.martin@example.com',   'Chris',   'Martin',   '1991-08-17', 'US', 'USD', 'active',    'partial', 'android', '2023-03-10 13:00:00', '2023-03-10 13:00:00'),
      (9,  'agarcia',   'a.garcia@example.com',   'Ana',     'Garcia',   '1989-12-03', 'US', 'USD', 'suspended', 'full',    'ios',     '2023-01-25 11:00:00', '2023-05-01 09:00:00'),
      (10, 'kwilliams', 'k.williams@example.com', 'Kevin',   'Williams', '1996-05-20', 'US', 'USD', 'active',    'none',    'web',     '2023-04-15 16:00:00', '2023-04-15 16:00:00'),
      (11, 'hmueller',  'h.mueller@example.com',  'Hans',    'Mueller',  '1984-01-10', 'DE', 'EUR', 'active',    'full',    'web',     '2023-01-05 08:00:00', '2023-01-05 08:00:00'),
      (12, 'kschmidt',  'k.schmidt@example.com',  'Klaus',   'Schmidt',  '1986-10-25', 'DE', 'EUR', 'active',    'full',    'ios',     '2023-02-01 10:30:00', '2023-02-01 10:30:00'),
      (13, 'sfischer',  's.fischer@example.com',  'Sophie',  'Fischer',  '1994-03-07', 'DE', 'EUR', 'active',    'partial', 'android', '2023-03-20 14:00:00', '2023-03-20 14:00:00'),
      (14, 'tweber',    't.weber@example.com',     'Thomas',  'Weber',    '1990-07-14', 'DE', 'EUR', 'active',    'full',    'web',     '2023-01-30 09:00:00', '2023-01-30 09:00:00'),
      (15, 'mwagner',   'm.wagner@example.com',   'Marie',   'Wagner',   '1997-09-02', 'DE', 'EUR', 'active',    'none',    'ios',     '2023-04-20 11:00:00', '2023-04-20 11:00:00')""",
    """INSERT INTO BETS (id, user_id, status, bet_type, sport, wager_amount, potential_payout, settled_amount, outcome, odds, currency_code, placed_at, settled_at) VALUES
      (1,  1,  'settled', 'single',      'football',   10.00, 22.00,  22.00,  'won',  2.20, 'GBP', '2024-01-15 10:30:00', '2024-01-15 16:00:00'),
      (2,  2,  'settled', 'accumulator', 'football',   5.00,  47.50,  47.50,  'won',  9.50, 'GBP', '2024-01-20 12:00:00', '2024-01-20 22:00:00'),
      (3,  6,  'settled', 'single',      'basketball', 25.00, 42.50,  42.50,  'won',  1.70, 'USD', '2024-01-18 19:00:00', '2024-01-18 23:00:00'),
      (4,  11, 'settled', 'single',      'tennis',     15.00, 31.50,  31.50,  'won',  2.10, 'EUR', '2024-01-22 14:00:00', '2024-01-22 18:00:00'),
      (5,  12, 'settled', 'single',      'football',   20.00, 34.00,  34.00,  'won',  1.70, 'EUR', '2024-01-25 15:30:00', '2024-01-25 22:00:00'),
      (6,  1,  'settled', 'single',      'tennis',     15.00, 27.00,  0.00,   'lost', 1.80, 'GBP', '2024-01-16 11:00:00', '2024-01-16 15:30:00'),
      (7,  4,  'settled', 'accumulator', 'football',   8.00,  96.00,  0.00,   'lost', 12.0, 'GBP', '2024-01-19 09:00:00', '2024-01-19 21:00:00'),
      (8,  7,  'settled', 'single',      'basketball', 30.00, 48.00,  0.00,   'lost', 1.60, 'USD', '2024-01-21 20:00:00', '2024-01-21 23:30:00'),
      (9,  14, 'settled', 'single',      'football',   10.00, 21.00,  0.00,   'lost', 2.10, 'EUR', '2024-01-23 16:00:00', '2024-01-23 21:00:00'),
      (10, 8,  'settled', 'single',      'tennis',     20.00, 38.00,  0.00,   'lost', 1.90, 'USD', '2024-01-26 13:00:00', '2024-01-26 17:00:00'),
      (11, 13, 'void',    'single',      'football',   12.00, 23.00,  12.00,  'void', 1.92, 'EUR', '2024-01-17 10:00:00', '2024-01-17 20:00:00'),
      (12, 2,  'open',    'single',      'football',   10.00, 19.00,  NULL,   NULL,   1.90, 'GBP', '2024-01-28 10:00:00', NULL),
      (13, 5,  'open',    'accumulator', 'football',   5.00,  62.50,  NULL,   NULL,   12.5, 'GBP', '2024-01-28 12:00:00', NULL),
      (14, 10, 'open',    'single',      'basketball', 20.00, 37.00,  NULL,   NULL,   1.85, 'USD', '2024-01-28 19:00:00', NULL),
      (15, 15, 'open',    'single',      'tennis',     8.00,  16.40,  NULL,   NULL,   2.05, 'EUR', '2024-01-28 14:00:00', NULL)""",
    """INSERT INTO TRANSACTIONS (id, user_id, bet_id, type, amount, balance_after, currency_code, processed_at, reference) VALUES
      (1,  1,  NULL, 'deposit',    100.00, 100.00, 'GBP', '2024-01-14 09:00:00', 'DEP-001'),
      (2,  1,  1,    'bet',        -10.00, 90.00,  'GBP', '2024-01-15 10:30:00', 'BET-001'),
      (3,  1,  1,    'winnings',    22.00, 112.00, 'GBP', '2024-01-15 16:00:00', 'WIN-001'),
      (4,  1,  6,    'bet',        -15.00, 97.00,  'GBP', '2024-01-16 11:00:00', 'BET-006'),
      (5,  2,  NULL, 'deposit',     50.00, 50.00,  'GBP', '2024-01-19 08:00:00', 'DEP-002'),
      (6,  2,  2,    'bet',         -5.00, 45.00,  'GBP', '2024-01-20 12:00:00', 'BET-002'),
      (7,  2,  2,    'winnings',    47.50, 92.50,  'GBP', '2024-01-20 22:00:00', 'WIN-002'),
      (8,  2,  12,   'bet',        -10.00, 82.50,  'GBP', '2024-01-28 10:00:00', 'BET-012'),
      (9,  4,  NULL, 'deposit',     80.00, 80.00,  'GBP', '2024-01-18 10:00:00', 'DEP-004'),
      (10, 4,  7,    'bet',         -8.00, 72.00,  'GBP', '2024-01-19 09:00:00', 'BET-007'),
      (11, 5,  NULL, 'deposit',     60.00, 60.00,  'GBP', '2024-01-27 09:00:00', 'DEP-005'),
      (12, 5,  13,   'bet',         -5.00, 55.00,  'GBP', '2024-01-28 12:00:00', 'BET-013'),
      (13, 6,  NULL, 'deposit',    200.00, 200.00, 'USD', '2024-01-17 10:00:00', 'DEP-006'),
      (14, 6,  3,    'bet',        -25.00, 175.00, 'USD', '2024-01-18 19:00:00', 'BET-003'),
      (15, 6,  3,    'winnings',    42.50, 217.50, 'USD', '2024-01-18 23:00:00', 'WIN-003'),
      (16, 7,  NULL, 'deposit',    150.00, 150.00, 'USD', '2024-01-20 09:00:00', 'DEP-007'),
      (17, 7,  8,    'bet',        -30.00, 120.00, 'USD', '2024-01-21 20:00:00', 'BET-008'),
      (18, 8,  NULL, 'deposit',    100.00, 100.00, 'USD', '2024-01-25 08:00:00', 'DEP-008'),
      (19, 8,  10,   'bet',        -20.00, 80.00,  'USD', '2024-01-26 13:00:00', 'BET-010'),
      (20, 10, NULL, 'deposit',    250.00, 250.00, 'USD', '2024-01-27 15:00:00', 'DEP-010'),
      (21, 10, 14,   'bet',        -20.00, 230.00, 'USD', '2024-01-28 19:00:00', 'BET-014'),
      (22, 11, NULL, 'deposit',    120.00, 120.00, 'EUR', '2024-01-21 08:00:00', 'DEP-011'),
      (23, 11, 4,    'bet',        -15.00, 105.00, 'EUR', '2024-01-22 14:00:00', 'BET-004'),
      (24, 11, 4,    'winnings',    31.50, 136.50, 'EUR', '2024-01-22 18:00:00', 'WIN-004'),
      (25, 12, NULL, 'deposit',    100.00, 100.00, 'EUR', '2024-01-24 09:00:00', 'DEP-012'),
      (26, 12, 5,    'bet',        -20.00, 80.00,  'EUR', '2024-01-25 15:30:00', 'BET-005'),
      (27, 12, 5,    'winnings',    34.00, 114.00, 'EUR', '2024-01-25 22:00:00', 'WIN-005'),
      (28, 12, NULL, 'withdrawal', -50.00, 64.00,  'EUR', '2024-01-26 10:00:00', 'WIT-012'),
      (29, 13, NULL, 'deposit',     75.00, 75.00,  'EUR', '2024-01-16 09:00:00', 'DEP-013'),
      (30, 13, 11,   'bet',        -12.00, 63.00,  'EUR', '2024-01-17 10:00:00', 'BET-011'),
      (31, 13, 11,   'refund',      12.00, 75.00,  'EUR', '2024-01-17 20:00:00', 'REF-011'),
      (32, 14, NULL, 'deposit',     90.00, 90.00,  'EUR', '2024-01-22 09:00:00', 'DEP-014'),
      (33, 14, 9,    'bet',        -10.00, 80.00,  'EUR', '2024-01-23 16:00:00', 'BET-009'),
      (34, 15, NULL, 'deposit',     50.00, 50.00,  'EUR', '2024-01-27 10:00:00', 'DEP-015'),
      (35, 15, 15,   'bet',         -8.00, 42.00,  'EUR', '2024-01-28 14:00:00', 'BET-015')""",
]


def main():
    con = snowflake.connector.connect(**CONN_PARAMS)
    cur = con.cursor()

    for label, statements in [("setup", SETUP_SQL), ("tables", TABLE_SQL), ("seed", SEED_SQL)]:
        for sql in statements:
            try:
                cur.execute(sql)
            except Exception as e:
                print(f"[{label}] Error executing SQL: {e}")
                print(f"  Statement: {sql[:80]}...")
                raise

    print("BETTING database seeded successfully.")
    cur.close()
    con.close()


if __name__ == "__main__":
    main()

main()
