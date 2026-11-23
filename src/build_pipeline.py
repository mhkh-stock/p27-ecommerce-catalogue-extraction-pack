"""Build the P27 catalogue warehouse: bronze -> silver -> gold.

Loads the scraped CSV into bronze, runs the silver cleaning model,
extracts screen size / RAM / storage from the description text
(SQLite has no regex, so this runs in Python), builds the gold star
schema + marts, computes medians and per-category IQR price fences
(SQLite has no percentile function), flags outliers, then exports
the fact table and marts as CSVs.

Usage:  python3 src/build_pipeline.py
"""
import csv
import re
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"

SCREEN_RE = re.compile(r'(\d+(?:\.\d+)?)\s?["\u2033]')
RAM_RE = re.compile(r'(\d+)\s?GB(?!\s*(?:SSD|HDD|eMMC|Flash))')
STORAGE_RE = re.compile(r'(\d+(?:\.\d+)?)\s?(GB|TB)\s?(SSD|HDD|eMMC|Flash)')


def parse_specs(description):
    """Screen size (inches), RAM (GB), storage (GB + type) from the
    listing description. Returns Nones where the listing does not
    state the spec — the site's short listings often omit storage."""
    screen = None
    m = SCREEN_RE.search(description)
    screen = float(m.group(1)) if m else None
    m = RAM_RE.search(description)
    ram = int(m.group(1)) if m else None
    storage, stype = None, None
    m = STORAGE_RE.search(description)
    if m:
        val = float(m.group(1))
        storage = val * 1024 if m.group(2) == "TB" else val
        stype = m.group(3)
    return screen, ram, storage, stype


def load_csv(conn, table, path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(cols)}) "
        f"VALUES ({', '.join('?' * len(cols))})",
        [[r[c] for c in cols] for r in rows])
    return len(rows)


def run_sql(conn, path):
    conn.executescript(Path(path).read_text(encoding="utf-8"))


def export_csv(conn, table, path):
    cur = conn.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    return len(rows)


def main():
    if DB.exists():
        DB.unlink()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)

    run_sql(conn, ROOT / "sql" / "schema.sql")
    n = load_csv(conn, "bronze_catalogue", RAW / "catalogue_SAMPLE.csv")
    print(f"bronze_catalogue: {n} rows")
    run_sql(conn, ROOT / "sql" / "silver_catalogue.sql")

    # Spec extraction from descriptions (Python regex).
    specs = {}
    for pid, desc in conn.execute("SELECT product_id, description FROM silver_catalogue"):
        specs[pid] = parse_specs(desc)
    for pid, (screen, ram, storage, stype) in specs.items():
        conn.execute(
            "UPDATE silver_catalogue SET screen_inches = ?, ram_gb = ?, "
            "storage_gb = ?, storage_type = ? WHERE product_id = ?",
            (screen, ram, storage, stype, pid))
    n_screen = sum(1 for v in specs.values() if v[0] is not None)
    n_ram = sum(1 for v in specs.values() if v[1] is not None)
    n_storage = sum(1 for v in specs.values() if v[2] is not None)
    print(f"specs parsed: screen {n_screen}/147, RAM {n_ram}/147, storage {n_storage}/147")

    run_sql(conn, ROOT / "sql" / "gold_dimensions.sql")
    run_sql(conn, ROOT / "sql" / "gold_facts.sql")
    run_sql(conn, ROOT / "sql" / "gold_marts.sql")

    # Medians (category + brand) and per-category IQR fences.
    prices_by_cat = {}
    prices_by_brand = {}
    for price, cat, brand in conn.execute(
            "SELECT price_usd, category, brand FROM silver_catalogue"):
        prices_by_cat.setdefault(cat, []).append(price)
        prices_by_brand.setdefault(brand, []).append(price)
    for cat, vals in prices_by_cat.items():
        conn.execute("UPDATE mart_price_by_category SET median_price_usd = ? "
                     "WHERE category = ?", (round(statistics.median(vals), 2), cat))
    for brand, vals in prices_by_brand.items():
        conn.execute("UPDATE mart_price_by_brand SET median_price_usd = ? "
                     "WHERE brand = ?", (round(statistics.median(vals), 2), brand))

    fences = {}
    for cat, vals in prices_by_cat.items():
        q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
        fence = round(q3 + 1.5 * (q3 - q1), 2)
        fences[cat] = (round(q1, 2), round(q3, 2), fence)
    outliers = 0
    for pid, title, cat, brand, price in conn.execute(
            "SELECT product_id, title, category, brand, price_usd "
            "FROM silver_catalogue"):
        q1, q3, fence = fences[cat]
        if price > fence:
            conn.execute(
                "INSERT INTO mart_price_outliers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, title, cat, brand, price, q1, q3, fence, round(price - fence, 2)))
            conn.execute("UPDATE fact_catalogue SET is_outlier = 1 WHERE product_id = ?",
                         (pid,))
            outliers += 1
    print(f"price outliers (per-category IQR): {outliers}")
    for cat, (q1, q3, fence) in sorted(fences.items()):
        print(f"  {cat}: Q1 ${q1:.2f} Q3 ${q3:.2f} fence ${fence:.2f}")
    conn.commit()

    n = export_csv(conn, "fact_catalogue", PROCESSED / "fact_catalogue.csv")
    print(f"fact_catalogue: {n} rows -> data/processed/fact_catalogue.csv")
    for table in ["mart_price_by_category", "mart_price_by_brand",
                  "mart_rating_by_category", "mart_price_bands",
                  "mart_price_outliers", "mart_top_reviewed"]:
        n = export_csv(conn, table, OUT / f"{table}.csv")
        print(f"{table}: {n} rows -> outputs/{table}.csv")

    for table in ["bronze_catalogue", "silver_catalogue", "fact_catalogue",
                  "dim_category", "dim_brand"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {n}")
    conn.close()
    print(f"wrote {DB}")


if __name__ == "__main__":
    main()
