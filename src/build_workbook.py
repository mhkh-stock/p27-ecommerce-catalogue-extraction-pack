"""Build the P27 client workbook: outputs/catalogue_SAMPLE.xlsx.

Sheets: Cover | Catalogue (147 products, filterable) | Summary
(headline numbers as LIVE formulas over Catalogue) | Price by
category | Price by brand | Ratings | Method. All numbers come
from src/headlines.py (the warehouse); the Summary sheet proves
them a second way with formulas, and src/checks.py recalculates
the workbook in LibreOffice and compares.

Usage:  python3 src/build_workbook.py
"""
import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from headlines import compute_headlines

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"
OUT = ROOT / "outputs" / "catalogue_SAMPLE.xlsx"

NAVY = "2E5A88"
LIGHT = "DCE6F1"
GREY = "F2F2F2"
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color=NAVY)
H_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
HDR_FILL = PatternFill("solid", fgColor=NAVY)
BAND_FILL = PatternFill("solid", fgColor=LIGHT)
MONEY = '#,##0.00'
MONEY0 = '"$"#,##0'
PCT = '0.00%'
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = H_FONT
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        cell.border = BOX


def money(cell, fmt=MONEY):
    cell.number_format = fmt


def main():
    conn = sqlite3.connect(DB)
    h = compute_headlines(conn)
    rows = conn.execute(
        "SELECT product_id, category, brand, title, price_usd, rating_stars, "
        "review_count, screen_inches, ram_gb, storage_gb, price_band, product_url "
        "FROM silver_catalogue ORDER BY category, brand, price_usd").fetchall()
    n = len(rows)
    last = n + 1  # last data row on Catalogue (header is row 1)
    conn.close()

    wb = Workbook()

    # ---------- Cover ----------
    ws = wb.active
    ws.title = "Cover"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToPage = True
    ws["A1"] = "E-commerce Catalogue Extraction Pack"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "Your competitor's catalogue, in a spreadsheet."
    ws["A2"].font = Font(name="Calibri", size=12, italic=True)
    ws["A3"] = ("SAMPLE delivery — scraped live from the webscraper.io "
                "e-commerce practice site on 23 Nov 2026. 147 products, "
                "3 categories, 16 brands. Prices in USD as listed; the site "
                "publishes no stock status, so none is claimed.")
    ws["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A3:F3")
    ws.row_dimensions[3].height = 45
    ws["A5"] = "Headline numbers (live — change the Catalogue sheet and these move)"
    ws["A5"].font = Font(name="Calibri", size=11, bold=True)
    cover_rows = [
        ("Products in catalogue", f"='Summary'!B3"),
        ("Categories", f"='Summary'!B4"),
        ("Brands", f"='Summary'!B5"),
        ("Catalogue value (USD)", f"='Summary'!B6"),
        ("Average price (USD)", f"='Summary'!B7"),
        ("Median price (USD)", f"='Summary'!B8"),
        ("Average rating (stars)", f"='Summary'!B11"),
        ("Total reviews", f"='Summary'!B14"),
    ]
    for i, (label, formula) in enumerate(cover_rows):
        r = 6 + i
        ws.cell(row=r, column=1, value=label)
        c = ws.cell(row=r, column=2, value=formula)
        if "price" in label.lower() or "value" in label.lower():
            money(c)
        if "rating" in label.lower():
            c.number_format = '0.00'
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18
    ws["A15"] = "How to use this file: Catalogue holds every product (filter it). " \
                "Summary proves the headline numbers with formulas. Price by " \
                "category / Price by brand / Ratings hold the analysis. Method " \
                "explains how the data was collected and what it cannot say."
    ws["A15"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A15:F15")
    ws.row_dimensions[15].height = 45

    # ---------- Catalogue ----------
    cat = wb.create_sheet("Catalogue")
    headers = ["Product ID", "Category", "Brand", "Title", "Price (USD)",
               "Rating", "Reviews", 'Screen (")', "RAM (GB)", "Storage (GB)",
               "Price band", "Product URL"]
    cat.append(headers)
    style_header(cat, 1, len(headers))
    for r in rows:
        cat.append(list(r))
    for row in cat.iter_rows(min_row=2, max_row=last, min_col=5, max_col=5):
        for c in row:
            money(c)
    for row in cat.iter_rows(min_row=2, max_row=last, min_col=12, max_col=12):
        for c in row:
            c.hyperlink = c.value
            c.font = Font(color=NAVY, underline="single", size=9)
    widths = [12, 11, 13, 46, 12, 8, 9, 10, 9, 12, 14, 60]
    for i, w in enumerate(widths, start=1):
        cat.column_dimensions[get_column_letter(i)].width = w
    cat.freeze_panes = "A2"
    cat.auto_filter.ref = f"A1:L{last}"
    cat.sheet_properties.pageSetUpPr.fitToPage = True
    cat.page_setup.orientation = "landscape"
    cat.page_setup.fitToWidth = 1

    # ---------- Summary (all formulas over Catalogue) ----------
    sm = wb.create_sheet("Summary")
    sm["A1"] = "Headline numbers — every value below is a formula over the Catalogue sheet"
    sm["A1"].font = Font(name="Calibri", size=11, bold=True)
    sm.merge_cells("A1:B1")
    R = f"Catalogue!A2:A{last}"
    CAT = f"Catalogue!B2:B{last}"
    PRICE = f"Catalogue!E2:E{last}"
    RATE = f"Catalogue!F2:F{last}"
    REV = f"Catalogue!G2:G{last}"
    BAND = f"Catalogue!K2:K{last}"
    metrics = [
        ("Products in catalogue", f"=ROWS({R})", None),
        ("Categories", f'=SUMPRODUCT(({CAT}<>"")/COUNTIF({CAT},{CAT}&""))', '0'),
        ("Brands", f'=SUMPRODUCT((Catalogue!C2:C{last}<>"")/COUNTIF(Catalogue!C2:C{last},Catalogue!C2:C{last}&""))', '0'),
        ("Catalogue value (USD)", f"=SUM({PRICE})", MONEY),
        ("Average price (USD)", f"=AVERAGE({PRICE})", MONEY),
        ("Median price (USD)", f"=MEDIAN({PRICE})", MONEY),
        ("Cheapest product (USD)", f"=MIN({PRICE})", MONEY),
        ("Most expensive product (USD)", f"=MAX({PRICE})", MONEY),
        ("Average rating (stars)", f"=AVERAGE({RATE})", '0.00'),
        ("Products rated 4+ stars", f'=COUNTIF({RATE},">=4")', '0'),
        ("Products rated 1 star", f'=COUNTIF({RATE},"=1")', '0'),
        ("Total reviews", f"=SUM({REV})", '0'),
        ("Products with no reviews", f'=COUNTIF({REV},"=0")', '0'),
        ("Average price — Laptops (USD)", f'=AVERAGEIF({CAT},"Laptops",{PRICE})', MONEY),
        ("Average price — Tablets (USD)", f'=AVERAGEIF({CAT},"Tablets",{PRICE})', MONEY),
        ("Average price — Touch (USD)", f'=AVERAGEIF({CAT},"Touch",{PRICE})', MONEY),
        ("Products under $300", f'=COUNTIF({BAND},"Under $300")', '0'),
        ("Products $300 - $599", f'=COUNTIF({BAND},"$300 - $599")', '0'),
        ("Products $600 - $999", f'=COUNTIF({BAND},"$600 - $999")', '0'),
        ("Products $1000 - $1499", f'=COUNTIF({BAND},"$1000 - $1499")', '0'),
        ("Products $1500+", f'=COUNTIF({BAND},"$1500+")', '0'),
    ]
    sm.append(["Metric", "Value"])
    style_header(sm, 2, 2)
    for label, formula, fmt in metrics:
        sm.append([label, formula])
        if fmt:
            sm.cell(row=sm.max_row, column=2).number_format = fmt
    sm.column_dimensions["A"].width = 34
    sm.column_dimensions["B"].width = 18
    sm["A25"] = ("Note: the site lists whole-star ratings only (1–4 stars in this "
                 "catalogue — no product is rated 5 stars) and publishes no stock "
                 "status, so this workbook makes no stock claim.")
    sm["A25"].alignment = Alignment(wrap_text=True, vertical="top")
    sm.merge_cells("A25:B25")
    sm.row_dimensions[25].height = 30

    # ---------- Price by category ----------
    pc = wb.create_sheet("Price by category")
    pc.append(["Category", "Products", "Min price (USD)", "Max price (USD)",
               "Mean price (USD)", "Median price (USD)", "Total value (USD)"])
    style_header(pc, 1, 7)
    for c in h["price_by_category"]:
        pc.append([c["category"], c["products"], c["min"], c["max"],
                   c["mean"], c["median"], c["total"]])
    total_row = pc.max_row + 1
    pc.cell(row=total_row, column=1, value="TOTAL")
    pc.cell(row=total_row, column=2, value=f"=SUM(B2:B{total_row - 1})")
    pc.cell(row=total_row, column=7, value=f"=SUM(G2:G{total_row - 1})")
    for col in range(3, 8):
        for row in pc.iter_rows(min_row=2, max_row=total_row, min_col=col, max_col=col):
            for cell in row:
                money(cell)
    for col in range(1, 8):
        pc.cell(row=total_row, column=col).font = Font(bold=True)
    pc.column_dimensions["A"].width = 12
    for col in "BCDEFG":
        pc.column_dimensions[col].width = 17

    # ---------- Price by brand ----------
    pb = wb.create_sheet("Price by brand")
    pb.append(["Brand", "Products", "Min price (USD)", "Max price (USD)",
               "Mean price (USD)", "Median price (USD)", "Avg rating", "Total reviews"])
    style_header(pb, 1, 8)
    for b in h["price_by_brand"]:
        pb.append([b["brand"], b["products"], b["min"], b["max"],
                   b["mean"], b["median"], b["avg_rating"], b["total_reviews"]])
    total_row = pb.max_row + 1
    pb.cell(row=total_row, column=1, value="TOTAL")
    pb.cell(row=total_row, column=2, value=f"=SUM(B2:B{total_row - 1})")
    pb.cell(row=total_row, column=8, value=f"=SUM(H2:H{total_row - 1})")
    for col in range(3, 7):
        for row in pb.iter_rows(min_row=2, max_row=total_row, min_col=col, max_col=col):
            for cell in row:
                money(cell)
    for row in pb.iter_rows(min_row=2, max_row=total_row, min_col=7, max_col=7):
        for cell in row:
            cell.number_format = '0.00'
    for col in range(1, 9):
        pb.cell(row=total_row, column=col).font = Font(bold=True)
    pb.column_dimensions["A"].width = 14
    for col in "BCDEFGH":
        pb.column_dimensions[col].width = 16

    # ---------- Ratings ----------
    rt = wb.create_sheet("Ratings")
    rt.append(["Stars", "Products", "Share"])
    style_header(rt, 1, 3)
    for d in h["rating_dist"]:
        rt.append([d["stars"], d["products"], None])
        r = rt.max_row
        rt.cell(row=r, column=3, value=f"=B{r}/SUM($B$2:$B$5)")
        rt.cell(row=r, column=3).number_format = PCT
    total_row = rt.max_row + 1
    rt.cell(row=total_row, column=1, value="TOTAL")
    rt.cell(row=total_row, column=2, value=f"=SUM(B2:B{total_row - 1})")
    rt.cell(row=total_row, column=3, value=f"=SUM(C2:C{total_row - 1})")
    rt.cell(row=total_row, column=3).number_format = PCT
    for col in range(1, 4):
        rt.cell(row=total_row, column=col).font = Font(bold=True)
    rt["A8"] = "Average rating by category"
    rt["A8"].font = Font(name="Calibri", size=11, bold=True)
    rt.append([])
    rt.append(["Category", "Products", "Avg rating", "Rated 4+", "Rated 1 star",
               "No reviews", "Total reviews", "Review-weighted rating"])
    style_header(rt, 10, 8)
    for c in h["rating_by_category"]:
        rt.append([c["category"], c["products"], c["avg_rating"], c["rated_4_plus"],
                   c["rated_1"], c["zero_reviews"], c["total_reviews"],
                   c["weighted_rating"]])
    for row in rt.iter_rows(min_row=11, max_row=rt.max_row, min_col=3, max_col=3):
        for cell in row:
            cell.number_format = '0.00'
    for row in rt.iter_rows(min_row=11, max_row=rt.max_row, min_col=8, max_col=8):
        for cell in row:
            cell.number_format = '0.00'
    rt.column_dimensions["A"].width = 12
    for col in "BCDEFGH":
        rt.column_dimensions[col].width = 16

    # ---------- Method ----------
    md = wb.create_sheet("Method")
    md["A1"] = "Method, definitions and limits"
    md["A1"].font = Font(name="Calibri", size=11, bold=True)
    lines = [
        "Source: webscraper.io e-commerce practice site (built for scraping "
        "practice), categories Laptops, Tablets and Touch, scraped 23 Nov 2026. "
        "One request per category page; each page lists every product.",
        "Price: USD as listed on the site, parsed from the listed price text.",
        "Brand: normalised from the listing title — sub-brands and model lines "
        "(ThinkPad, Aspire, Galaxy, Hewlett, Pavilion, ProBook, Inspiron, "
        "IdeaTab, iPad, iPhone, Iconia, MeMO) are mapped to their maker.",
        "Rating: whole stars 1–5 as listed. This catalogue holds no 5-star "
        "product; the average is 2.37 stars.",
        "Reviews: the review count shown on each listing (0–14).",
        "Price bands: Under $300 / $300–$599 / $600–$999 / $1000–$1499 / $1500+.",
        "Outliers: per-category IQR fence (Q3 + 1.5 × IQR). No product in this "
        "catalogue is priced above its category fence — 0 outliers.",
        "Specs (screen, RAM, storage) are parsed from the listing description "
        "where stated: screen 134/147, RAM 135/147, storage 87/147. Blank "
        "means the listing does not state it, not zero.",
        "Limits: the site publishes no stock status, no seller name and no "
        "sales volume, so none of those are in this pack. Prices are a "
        "single-day snapshot (23 Nov 2026) — re-run src/scrape.py for a "
        "fresh snapshot.",
        "Reproduce: python3 src/scrape.py, then src/build_pipeline.py, "
        "src/run_tests.py, src/build_chart.py, src/build_workbook.py, "
        "src/build_report.py, src/checks.py.",
    ]
    for i, line in enumerate(lines):
        r = 3 + i
        md.cell(row=r, column=1, value=f"•  {line}")
        md.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        md.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        md.row_dimensions[r].height = 30
    md.column_dimensions["A"].width = 110

    wb.save(OUT)
    print(f"wrote {OUT} ({n} products, 7 sheets)")


if __name__ == "__main__":
    main()
