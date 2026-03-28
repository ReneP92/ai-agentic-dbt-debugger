"""Print schema and 10 random rows for every table in the BETTING database."""

import time
import snowflake.connector

CONN_PARAMS = dict(
    host="snowflake.localhost.localstack.cloud",
    port=4566,
    account="localstack",
    user="test",
    password="test",
    database="BETTING",
    protocol="https",
)

MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds


def run(cur, sql):
    cur.execute(sql)
    return cur.fetchall(), [d[0] for d in cur.description]


def print_table(rows, headers):
    if not rows:
        print("  (empty)")
        return
    widths = [max(len(str(h)), max(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  " + "  ".join("-" * w for w in widths)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(v) if v is not None else "NULL" for v in row]))


def connect_with_retry():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            con = snowflake.connector.connect(**CONN_PARAMS)
            # Verify the database is accessible
            cur = con.cursor()
            cur.execute("SELECT CURRENT_DATABASE()")
            return con, cur
        except snowflake.connector.errors.ProgrammingError as e:
            if attempt < MAX_RETRIES:
                print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                print(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def main():
    con, cur = connect_with_retry()

    tables, _ = run(
        cur,
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE (TABLE_TYPE = 'BASE TABLE' OR TABLE_TYPE = 'VIEW') "
        "AND TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'LS_INFORMATION_SCHEMA', 'PG_CATALOG', 'PUBLIC') "
        "AND TABLE_SCHEMA NOT LIKE 'pg_%%' "
        "ORDER BY TABLE_SCHEMA, TABLE_NAME",
    )

    if not tables:
        print("No tables found.")
        return

    for schema, table in tables:
        fqn = f'"{schema}"."{table}"'
        print(f"\n{'='*60}")
        print(f"  {schema}.{table}")
        print(f"{'='*60}")

        print("\n-- Schema --")
        rows, headers = run(cur, f"DESCRIBE TABLE {fqn}")
        print_table(rows, headers)

        print("\n-- Sample (up to 10 random rows) --")
        rows, headers = run(cur, f"SELECT * FROM {fqn} ORDER BY RANDOM() LIMIT 10")
        print_table(rows, headers)

    cur.close()
    con.close()


if __name__ == "__main__":
    main()
