import sqlite3

DB = "data/hexagrandhouse_cloud_runtime.db"

conn = sqlite3.connect(DB)

for table in ["lottery_base_features", "lottery_predictions", "lottery_daily_latest_results"]:
    print("\n" + "=" * 60)
    print(table)
    print("=" * 60)

    cols = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
    print("Columns:")
    print(cols)

    row = conn.execute(f'SELECT * FROM "{table}" LIMIT 1').fetchone()
    print("\nSample row:")
    print(row)

conn.close()
