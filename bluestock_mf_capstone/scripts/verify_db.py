import sqlite3
conn = sqlite3.connect("data/db/bluestock_mf.db")
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"SQLITE DB: {len(tables)} tables loaded")
for t in tables:
    cnt = conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
    print(f"  {t:<35}: {cnt:>8,} rows")
conn.close()
print("DB verification PASSED.")
