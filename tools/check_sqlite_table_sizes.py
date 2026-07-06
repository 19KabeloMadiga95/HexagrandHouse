import sqlite3
import tempfile
import os

SRC = "data/hexagrandhouse.db"

con = sqlite3.connect(SRC)
tables = [
    r[0]
    for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
]

results = []
tmpdir = tempfile.mkdtemp()

print("Checking table sizes...")
print("This may take a few minutes.\n")

for table in tables:
    temp_db = os.path.join(tmpdir, table + ".db")

    dst = sqlite3.connect(temp_db)
    dst.execute("ATTACH DATABASE ? AS src", (SRC,))
    dst.execute(f'CREATE TABLE "{table}" AS SELECT * FROM src."{table}"')
    dst.commit()
    dst.execute("VACUUM")
    dst.close()

    size_mb = os.path.getsize(temp_db) / 1024 / 1024
    results.append((table, size_mb))

    os.remove(temp_db)

con.close()

for table, size_mb in sorted(results, key=lambda x: x[1], reverse=True)[:30]:
    print(f"{table}: {size_mb:.2f} MB")
