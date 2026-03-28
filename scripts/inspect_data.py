"""Print schema and 10 random rows for every table in the BETTING database."""

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


def main():
    con = snowflake.connector.connect(**CONN_PARAMS)
    cur = con.cursor()

    tables, _ = run(
        cur,
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE = 'BASE TABLE' OR TABLE_TYPE = 'VIEW' "
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
