import sqlite3

DB = "data/hexagrandhouse_cloud_runtime.db"

conn = sqlite3.connect(DB)

conn.execute('DROP TABLE IF EXISTS lottery_history')

conn.execute("""
CREATE TABLE lottery_history AS
SELECT
    GameFamily,
    GameName,
    DrawType,
    DrawDate,
    DrawDay,
    DrawNumber,
    N1,
    N2,
    N3,
    N4,
    N5,
    N6,
    Bonus,
    NumberCount,
    RegularSum,
    OddCount,
    EvenCount,
    LowCount,
    HighCount,
    RegularRange,
    BonusRange,
    SourceName,
    SourceUrl,
    RecordKey
FROM lottery_base_features
""")

conn.commit()

rows = conn.execute("SELECT COUNT(*) FROM lottery_history").fetchone()[0]
conn.execute("VACUUM")
conn.close()

print(f"lottery_history created. Rows: {rows}")
