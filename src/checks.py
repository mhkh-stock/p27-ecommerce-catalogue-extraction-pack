"""P27 — verification suite. Recomputes every headline number from
the raw CSV independently (no database, no warehouse code) and
compares it with the warehouse, the workbook (recalculated in
LibreOffice), the report PDF and the README. A mistake in any one
of the four shows up as a failure.

Also checks: file inventory, chart PNGs, test_results.json (14/14),
scrape log consistency, spec coverage, and that the .db is gitignored.

Usage:  python3 src/checks.py   (expect all checks passing)
"""
import csv
import json
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"
RAW = ROOT / "data" / "raw" / "catalogue_SAMPLE.csv"
OUT = ROOT / "outputs"
XLSX = OUT / "catalogue_SAMPLE.xlsx"
PDF = OUT / "catalogue_report_SAMPLE.pdf"

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def close(a, b, tol=0.01):
    return abs(a - b) <= tol


def main():
    # ---- 1. Independent recompute from the raw CSV ----
    with open(RAW, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    prices = [float(r["price_usd_raw"].replace("$", "").replace(",", "")) for r in raw]
    ratings = [int(r["rating_stars"]) for r in raw]
    reviews = [int(r["review_count"]) for r in raw]
    cats = [r["category"] for r in raw]
    ids = [r["product_id"] for r in raw]

    exp = {
        "products": len(raw),
        "categories": len(set(cats)),
        "total_value": round(sum(prices), 2),
        "price_min": min(prices),
        "price_max": max(prices),
        "price_mean": round(statistics.mean(prices), 2),
        "price_median": round(statistics.median(prices), 2),
        "avg_rating": round(statistics.mean(ratings), 2),
        "total_reviews": sum(reviews),
        "rated_4_plus": sum(1 for x in ratings if x >= 4),
        "rated_1": sum(1 for x in ratings if x == 1),
        "rated_5": sum(1 for x in ratings if x == 5),
        "zero_reviews": sum(1 for x in reviews if x == 0),
    }
    check("raw: 147 rows", exp["products"] == 147, f"got {exp['products']}")
    check("raw: no duplicate product_id", len(set(ids)) == len(ids))
    check("raw: no missing fields",
          all(v.strip() for r in raw for v in r.values()))
    check("raw: 3 categories", exp["categories"] == 3)
    check("raw: category counts 117/21/9",
          cats.count("Laptops") == 117 and cats.count("Tablets") == 21
          and cats.count("Touch") == 9,
          f"{cats.count('Laptops')}/{cats.count('Tablets')}/{cats.count('Touch')}")
    check("raw: prices all positive", all(p > 0 for p in prices))
    check("raw: ratings 1-4 only (no 5-star product)",
          min(ratings) == 1 and max(ratings) == 4 and exp["rated_5"] == 0)

    # Expected brand count, normalised independently in Python with
    # the same mapping rules as the silver SQL (a second implementation
    # of the map, so a SQL mapping slip shows up here).
    def norm_brand(title):
        t = title
        if t.startswith(("ThinkPad", "Lenovo", "IdeaTab")):
            return "Lenovo"
        if t.startswith(("Aspire", "Acer", "Iconia")):
            return "Acer"
        if t.startswith(("Hewlett", "HP ", "Pavilion", "ProBook")):
            return "HP"
        if t.startswith(("Dell", "Inspiron")):
            return "Dell"
        if t.startswith(("Apple", "Iphone", "iPad")):
            return "Apple"
        if t.startswith(("Samsung", "Galaxy")):
            return "Samsung"
        if t.startswith(("Asus", "MeMO", "MeMo", "Memo")):
            return "Asus"
        if t.startswith("Packard"):
            return "Packard Bell"
        return t.split(" ", 1)[0]

    exp["brands"] = len({norm_brand(r["title"]) for r in raw})
    check("raw: 16 brands after normalisation", exp["brands"] == 16,
          f"got {exp['brands']}")

    # scrape log agrees with the raw file
    log = json.loads((ROOT / "data" / "raw" / "scrape_log.json").read_text())
    check("scrape log: total matches raw rows",
          log["total_products"] == len(raw), str(log["total_products"]))
    check("scrape log: per-category counts match",
          {c["category"]: c["products"] for c in log["categories"]}
          == {"Laptops": 117, "Tablets": 21, "Touch": 9})
    check("scrape log: all HTTP 200",
          all(c["http_status"] == 200 for c in log["categories"]))

    # ---- 2. Warehouse agrees with the independent recompute ----
    conn = sqlite3.connect(DB)
    db = {
        "products": conn.execute("SELECT COUNT(*) FROM fact_catalogue").fetchone()[0],
        "categories": conn.execute("SELECT COUNT(*) FROM dim_category").fetchone()[0],
        "brands": conn.execute("SELECT COUNT(*) FROM dim_brand").fetchone()[0],
        "total_value": round(conn.execute("SELECT SUM(price_usd) FROM fact_catalogue").fetchone()[0], 2),
        "price_min": conn.execute("SELECT MIN(price_usd) FROM fact_catalogue").fetchone()[0],
        "price_max": conn.execute("SELECT MAX(price_usd) FROM fact_catalogue").fetchone()[0],
        "price_mean": round(conn.execute("SELECT AVG(price_usd) FROM fact_catalogue").fetchone()[0], 2),
        "avg_rating": round(conn.execute("SELECT AVG(rating_stars) FROM fact_catalogue").fetchone()[0], 2),
        "total_reviews": conn.execute("SELECT SUM(review_count) FROM fact_catalogue").fetchone()[0],
        "rated_4_plus": conn.execute("SELECT COUNT(*) FROM fact_catalogue WHERE rating_stars >= 4").fetchone()[0],
        "rated_1": conn.execute("SELECT COUNT(*) FROM fact_catalogue WHERE rating_stars = 1").fetchone()[0],
        "zero_reviews": conn.execute("SELECT COUNT(*) FROM fact_catalogue WHERE review_count = 0").fetchone()[0],
    }
    for key in ["products", "categories", "total_value", "price_min",
                "price_max", "price_mean", "avg_rating", "total_reviews",
                "rated_4_plus", "rated_1", "zero_reviews"]:
        check(f"db matches raw: {key}",
              close(db[key], exp[key]) if isinstance(exp[key], float) else db[key] == exp[key],
              f"db={db[key]} raw={exp[key]}")
    check("db: 16 brands", db["brands"] == 16, str(db["brands"]))
    vals = [r[0] for r in conn.execute("SELECT price_usd FROM fact_catalogue")]
    check("db: median price 739.99",
          close(statistics.median(vals), exp["price_median"]),
          str(statistics.median(vals)))
    check("db: silver = fact row counts",
          conn.execute("SELECT COUNT(*) FROM silver_catalogue").fetchone()[0]
          == conn.execute("SELECT COUNT(*) FROM fact_catalogue").fetchone()[0])
    check("db: marts reconcile (category products sum)",
          conn.execute("SELECT SUM(products) FROM mart_price_by_category").fetchone()[0] == 147)
    check("db: marts reconcile (category value sum)",
          close(conn.execute("SELECT SUM(total_value_usd) FROM mart_price_by_category").fetchone()[0],
                exp["total_value"]))
    check("db: marts reconcile (band products sum)",
          conn.execute("SELECT SUM(products) FROM mart_price_bands").fetchone()[0] == 147)
    check("db: 0 IQR outliers",
          conn.execute("SELECT COUNT(*) FROM mart_price_outliers").fetchone()[0] == 0)
    check("db: top-reviewed mart has 15 rows",
          conn.execute("SELECT COUNT(*) FROM mart_top_reviewed").fetchone()[0] == 15)
    # brand normalisation: no raw sub-brand survives
    bad = conn.execute(
        "SELECT COUNT(*) FROM silver_catalogue WHERE brand IN "
        "('ThinkPad','Aspire','Galaxy','Hewlett','Pavilion','ProBook',"
        "'Inspiron','IdeaTab','Iphone','iPad','Iconia','Memo','MeMO','MeMo',"
        "'Packard')").fetchone()[0]
    check("db: brand normalisation complete", bad == 0, f"{bad} unmapped")
    check("db: top brands are Lenovo 30 / Acer 29",
          conn.execute("SELECT products FROM mart_price_by_brand WHERE brand='Lenovo'").fetchone()[0] == 30
          and conn.execute("SELECT products FROM mart_price_by_brand WHERE brand='Acer'").fetchone()[0] == 29)
    # spec coverage
    cov = {
        "screen": conn.execute("SELECT COUNT(*) FROM silver_catalogue WHERE screen_inches IS NOT NULL").fetchone()[0],
        "ram": conn.execute("SELECT COUNT(*) FROM silver_catalogue WHERE ram_gb IS NOT NULL").fetchone()[0],
        "storage": conn.execute("SELECT COUNT(*) FROM silver_catalogue WHERE storage_gb IS NOT NULL").fetchone()[0],
    }
    check("db: spec coverage screen 134", cov["screen"] == 134, str(cov["screen"]))
    check("db: spec coverage RAM 135", cov["ram"] == 135, str(cov["ram"]))
    check("db: spec coverage storage 87", cov["storage"] == 87, str(cov["storage"]))
    # per-category means/medians used in the report
    cat_stats = {r[0]: r[1:] for r in conn.execute(
        "SELECT category, mean_price_usd, median_price_usd FROM mart_price_by_category")}
    check("db: laptops mean 909.39 / median 1102.66",
          close(cat_stats["Laptops"][0], 909.39) and close(cat_stats["Laptops"][1], 1102.66),
          str(cat_stats["Laptops"]))
    check("db: tablets mean 232.04 / median 130.99",
          close(cat_stats["Tablets"][0], 232.04) and close(cat_stats["Tablets"][1], 130.99),
          str(cat_stats["Tablets"]))
    check("db: touch mean 400.66 / median 118.99",
          close(cat_stats["Touch"][0], 400.66) and close(cat_stats["Touch"][1], 118.99),
          str(cat_stats["Touch"]))
    # price-band counts
    bands = dict(conn.execute("SELECT price_band, products FROM mart_price_bands").fetchall())
    check("db: price bands 23/45/14/62/3",
          bands == {"Under $300": 23, "$300 - $599": 45, "$600 - $999": 14,
                    "$1000 - $1499": 62, "$1500+": 3}, str(bands))
    # rating distribution
    dist = dict(conn.execute("SELECT rating_stars, COUNT(*) FROM fact_catalogue GROUP BY rating_stars").fetchall())
    check("db: rating distribution 43/33/44/27",
          dist == {1: 43, 2: 33, 3: 44, 4: 27}, str(dist))
    # 1-star products cost more on average than 4-star ones (report claim)
    avg1 = conn.execute("SELECT AVG(price_usd) FROM fact_catalogue WHERE rating_stars=1").fetchone()[0]
    avg4 = conn.execute("SELECT AVG(price_usd) FROM fact_catalogue WHERE rating_stars=4").fetchone()[0]
    check("db: 1-star avg price ($901.85) > 4-star ($673.80)",
          close(avg1, 901.85) and close(avg4, 673.80), f"{avg1:.2f} vs {avg4:.2f}")
    conn.close()

    # ---- 3. analysis.json agrees ----
    analysis = json.loads((OUT / "analysis.json").read_text())
    for key in ["products", "categories", "brands", "total_value_usd",
                "price_min", "price_max", "price_mean", "price_median",
                "avg_rating", "total_reviews", "rated_4_plus", "rated_1",
                "zero_reviews"]:
        raw_key = key.replace("_usd", "")
        check(f"analysis.json matches raw: {key}",
              close(analysis[key], exp[raw_key]) if isinstance(exp[raw_key], float)
              else analysis[key] == exp[raw_key],
              f"{analysis[key]} vs {exp[raw_key]}")

    # ---- 4. test_results.json ----
    tests = json.loads((OUT / "test_results.json").read_text())
    check("test_results.json: 14/14 passing",
          tests["total"] == 14 and tests["passed"] == 14,
          f"{tests['passed']}/{tests['total']}")
    check("test_results.json: no FAIL entries",
          all(t["status"] == "PASS" for t in tests["tests"]))

    # ---- 5. Workbook: LibreOffice recalc ----
    recalc_dir = OUT / ".recalc"
    if recalc_dir.exists():
        shutil.rmtree(recalc_dir)
    recalc_dir.mkdir()
    r = subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx",
                        "--outdir", str(recalc_dir), str(XLSX)],
                       capture_output=True, text=True, timeout=180)
    check("libreoffice recalc ran", r.returncode == 0, r.stderr.strip()[:200])
    recalc = recalc_dir / XLSX.name
    wb = load_workbook(recalc, data_only=True)
    check("workbook: 7 sheets",
          wb.sheetnames == ["Cover", "Catalogue", "Summary", "Price by category",
                            "Price by brand", "Ratings", "Method"],
          str(wb.sheetnames))
    cat_ws = wb["Catalogue"]
    check("workbook: Catalogue has 147 products + header",
          cat_ws.max_row == 148, str(cat_ws.max_row))
    check("workbook: Catalogue price sum matches",
          close(sum(c.value for c in cat_ws["E"][1:]), exp["total_value"]),
          str(sum(c.value for c in cat_ws["E"][1:])))
    sm = wb["Summary"]
    expected_summary = {
        "B3": 147, "B4": 3, "B5": 16, "B6": 114877.78, "B7": 781.48,
        "B8": 739.99, "B9": 24.99, "B10": 1799.0, "B11": 2.37, "B12": 27,
        "B13": 43, "B14": 1033, "B15": 8, "B16": 909.39, "B17": 232.04,
        "B18": 400.66, "B19": 23, "B20": 45, "B21": 14, "B22": 62, "B23": 3,
    }
    for cell, val in expected_summary.items():
        got = sm[cell].value
        ok = close(got, val) if isinstance(val, float) else got == val
        check(f"workbook Summary {cell} = {val}", ok, f"got {got}")
    # no error values anywhere in the recalculated workbook
    errors = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("#"):
                    errors.append(f"{ws.title}!{c.coordinate}={c.value}")
    check("workbook: zero error values after recalc", not errors, "; ".join(errors[:5]))
    cv = wb["Cover"]
    check("workbook Cover B6 (products) = 147", cv["B6"].value == 147, str(cv["B6"].value))
    check("workbook Cover B9 (value) matches",
          close(cv["B9"].value, 114877.78), str(cv["B9"].value))
    # formulas really are formulas (not pasted values) in the source file
    wb_src = load_workbook(XLSX, data_only=False)
    check("workbook source: Summary values are formulas",
          isinstance(wb_src["Summary"]["B3"].value, str)
          and wb_src["Summary"]["B3"].value.startswith("="))
    check("workbook source: Cover values are formulas",
          isinstance(wb_src["Cover"]["B6"].value, str)
          and wb_src["Cover"]["B6"].value.startswith("="))
    shutil.rmtree(recalc_dir)

    # ---- 6. Charts ----
    for name in ["avg_price_by_category.png", "price_band_distribution.png",
                 "avg_rating_by_brand.png"]:
        p = OUT / name
        ok = p.exists() and p.stat().st_size > 10000 \
            and p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        check(f"chart exists and is a PNG: {name}", ok,
              f"{p.stat().st_size if p.exists() else 0} bytes")

    # ---- 7. PDF report ----
    check("report PDF exists", PDF.exists() and PDF.stat().st_size > 1000)
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True)
    pages = re.search(r"Pages:\s+(\d+)", info.stdout)
    check("report PDF is 2 pages", pages and pages.group(1) == "2",
          pages.group(0) if pages else info.stderr[:100])
    text = subprocess.run(["pdftotext", str(PDF), "-"],
                          capture_output=True, text=True).stdout
    for needle in ["147", "$114,877.78", "2.37 stars", "$1,799.00",
                   "29.25%", "$600–$999", "no price outliers", "Asus ROG Strix SCAR"]:
        check(f"report PDF contains {needle!r}", needle in text)

    # ---- 8. File inventory + repo hygiene ----
    for rel in ["README.md", "PACKAGE-NOTE.md", "requirements.txt",
                ".gitignore", "data/README.md", "data/raw/catalogue_SAMPLE.csv",
                "data/raw/scrape_log.json", "data/processed/fact_catalogue.csv",
                "sql/schema.sql", "sql/silver_catalogue.sql",
                "sql/gold_dimensions.sql", "sql/gold_facts.sql",
                "sql/gold_marts.sql", "src/scrape.py", "src/build_pipeline.py",
                "src/run_tests.py", "src/build_chart.py",
                "src/build_workbook.py", "src/build_report.py",
                "src/headlines.py", "src/checks.py",
                "outputs/analysis.json", "outputs/test_results.json",
                "outputs/dq_report.md"]:
        check(f"file exists: {rel}", (ROOT / rel).exists())
    for name in ["mart_price_by_category.csv", "mart_price_by_brand.csv",
                 "mart_rating_by_category.csv", "mart_price_bands.csv",
                 "mart_price_outliers.csv", "mart_top_reviewed.csv"]:
        check(f"mart CSV exists: {name}", (OUT / name).exists())
    check("tests dir has 14 SQL files",
          len(list((ROOT / "sql" / "tests").glob("*.sql"))) == 14)
    gitignore = (ROOT / ".gitignore").read_text()
    check(".gitignore excludes *.db", "*.db" in gitignore)
    check(".db exists locally (never uploaded)", DB.exists())
    req = (ROOT / "requirements.txt").read_text()
    for pkg in ["requests==", "beautifulsoup4==", "openpyxl==",
                "reportlab==", "matplotlib=="]:
        check(f"requirements pins {pkg}", pkg in req)

    # ---- 9. README numbers match the verified outputs ----
    readme = (ROOT / "README.md").read_text()
    for needle in ["147", "3 categories", "16 brands", "$114,877.78",
                   "$24.99", "$1,799.00", "$781.48", "$739.99", "2.37",
                   "1,033", "14/14", "0 outliers", "117", "21", "9"]:
        check(f"README contains {needle!r}", needle in readme)

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"\n{passed}/{total} checks passing")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
