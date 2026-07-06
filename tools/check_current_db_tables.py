import sqlite3
from pathlib import Path

DB = Path("data/hexagrandhouse.db")

if not DB.exists():
    raise FileNotFoundError(f"Database not found: {DB}")

conn = sqlite3.connect(DB)
tables = [
    row[0]
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
]

print(f"Database: {DB}")
print(f"Size MB : {DB.stat().st_size / 1024 / 1024:.2f}")
print(f"Tables  : {len(tables)}")
print()
print("First 30 tables:")
for table in tables[:30]:
    print(table)

print()
for table in ["lottery_history", "football_history", "football_predictions", "football_ensemble_predictions"]:
    exists = table in tables
    if exists:
        count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        print(f"{table}: exists, rows={count}")
    else:
        print(f"{table}: missing")

conn.close()
