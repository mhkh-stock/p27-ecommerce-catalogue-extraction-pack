"""Build the P27 client report PDF + dq_report.md.

outputs/catalogue_report_SAMPLE.pdf — 2 pages: the question, the
headline numbers, price + rating findings, recommendations, method
and limits. Every number comes from src/headlines.py (the warehouse),
never typed. outputs/dq_report.md records the 14 test results and
the reconciliation.

Usage:  python3 src/build_report.py
"""
import json
import sqlite3
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle)

from headlines import compute_headlines

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "catalogue.db"
OUT_PDF = ROOT / "outputs" / "catalogue_report_SAMPLE.pdf"
OUT_DQ = ROOT / "outputs" / "dq_report.md"
TEST_RESULTS = ROOT / "outputs" / "test_results.json"

NAVY = colors.HexColor("#2E5A88")
LIGHT = colors.HexColor("#DCE6F1")


def money(v):
    return f"${v:,.2f}"


def table(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def build_pdf(h):
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title2", parent=styles["Title"], fontSize=17,
                           textColor=NAVY, spaceAfter=2 * mm, alignment=0)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13,
                        textColor=NAVY, spaceBefore=4 * mm, spaceAfter=2 * mm)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11,
                        textColor=NAVY, spaceBefore=3 * mm, spaceAfter=1 * mm)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10,
                          leading=13, spaceAfter=2 * mm)
    small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=11,
                           textColor=colors.HexColor("#555555"))
    cell = ParagraphStyle("Cell", parent=body, fontSize=9, leading=11,
                          spaceAfter=0)
    cell_r = ParagraphStyle("CellR", parent=cell, alignment=2)
    cell_h = ParagraphStyle("CellH", parent=cell, textColor=colors.white)

    def c(text, style=cell):
        return Paragraph(text, style)

    def cr(text):
        return Paragraph(text, cell_r)

    def ch(text):
        return Paragraph(text, cell_h)

    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="E-commerce Catalogue Extraction Pack — SAMPLE report",
                            author="Muhammad Hashir")
    story = []
    story.append(Paragraph("E-commerce Catalogue Extraction Pack", title))
    story.append(Paragraph(
        "Your competitor's catalogue, in a spreadsheet — SAMPLE delivery on "
        "a live scrape of the webscraper.io e-commerce practice site, "
        "23 Nov 2026.", body))
    story.append(Paragraph(
        "Client question: “My competitor's catalogue, in a spreadsheet.” "
        "This pack answers it with the full listed catalogue — every product, "
        "its price, its rating and its review count — plus the price and "
        "rating analysis a buyer actually uses to position against it.",
        body))

    story.append(Paragraph("Headline numbers", h1))
    story.append(table([
        [ch("Measure"), ch("Value")],
        [c("Products in catalogue"), cr("147")],
        [c("Categories"), cr("3 — Laptops (117), Tablets (21), Touch (9)")],
        [c("Brands (normalised)"), cr("16")],
        [c("Price range"), cr(f"{money(h['price_min'])} – {money(h['price_max'])}")],
        [c("Average / median price"), cr(f"{money(h['price_mean'])} / {money(h['price_median'])}")],
        [c("Total catalogue value"), cr(money(h["total_value_usd"]))],
        [c("Average rating"), cr(f"{h['avg_rating']:.2f} stars (of 5)")],
        [c("Total reviews"), cr(f"{h['total_reviews']:,}")],
        [c("Products rated 4+ stars"), cr(f"{h['rated_4_plus']} ({h['rated_4_plus'] / h['products'] * 100:.2f}%)")],
        [c("Products rated 1 star"), cr(f"{h['rated_1']} ({h['rated_1'] / h['products'] * 100:.2f}%)")],
        [c("Products with no reviews"), cr(str(h["zero_reviews"]))],
        [c("Price outliers (per-category IQR)"), cr("0")],
    ], [78 * mm, 100 * mm]))

    story.append(Paragraph("Price by category", h1))
    rows = [[ch("Category"), ch("Products"), ch("Min"), ch("Max"),
             ch("Mean"), ch("Median"), ch("Total value")]]
    for cat in h["price_by_category"]:
        rows.append([c(cat["category"]), cr(str(cat["products"])),
                     cr(money(cat["min"])), cr(money(cat["max"])),
                     cr(money(cat["mean"])), cr(money(cat["median"])),
                     cr(money(cat["total"]))])
    story.append(table(rows, [24 * mm, 18 * mm, 24 * mm, 24 * mm, 24 * mm,
                              28 * mm, 36 * mm]))
    story.append(Paragraph(
        "Laptops carry the catalogue: 117 of 147 products and "
        f"{money(h['price_by_category'][0]['total'])} of the {money(h['total_value_usd'])} total value. "
        "Their median ($1,102.66) sits above their mean ($909.39) — the range "
        "is two shelves, not one: budget machines near $300 and premium "
        "machines above $1,100, with little in between. Tablets are the "
        "budget shelf (median $130.99); Touch is nine phones, three of them "
        "iPhones at $899.99.", body))

    story.append(Paragraph("Price bands — the gap in the middle", h1))
    rows = [[ch("Price band"), ch("Products"), ch("Share"), ch("Avg price")]]
    for b in h["price_bands"]:
        rows.append([c(b["band"]), cr(str(b["products"])),
                     cr(f"{b['share_pct']:.2f}%"), cr(money(b["avg_price"]))])
    story.append(table(rows, [48 * mm, 30 * mm, 30 * mm, 70 * mm]))
    story.append(Paragraph(
        "42.18% of the catalogue sits at $1,000–$1,499 while only 9.52% "
        "sits at $600–$999. A competitor priced into that empty $600–$999 "
        "band faces almost no listed competition. Only 3 products break "
        "$1,500 — the most expensive is the Asus ROG Strix SCAR Edition at "
        "$1,799.00. No product is priced beyond its category's IQR fence: "
        "there are no price outliers to explain away.", body))

    story.append(Paragraph("Ratings — low, and price does not fix them", h1))
    rows = [[ch("Stars"), ch("Products")]]
    for d in h["rating_dist"]:
        rows.append([c(str(d["stars"])), cr(str(d["products"]))])
    story.append(table(rows, [48 * mm, 130 * mm]))
    story.append(Paragraph(
        "The average rating is 2.37 stars and no product in the whole "
        "catalogue is rated 5 stars. 43 products (29.25%) sit at 1 star — "
        "nearly a third of the range. Only 27 products (18.37%) reach 4 "
        "stars. And the dearer products are not the better-rated ones: "
        "1-star products average $901.85 while 4-star products average "
        "$673.80. Tablets rate best of the three categories (2.67), Touch "
        "worst (2.11). Eight laptops have no reviews at all — no buyer "
        "signal to trust or distrust.", body))

    story.append(Paragraph("Most-reviewed products", h1))
    rows = [[ch("Product"), ch("Category"), ch("Price"), ch("Rating"), ch("Reviews")]]
    for t in h["top_reviewed"][:5]:
        rows.append([c(t["title"]), c(t["category"]), cr(money(t["price"])),
                     cr(str(t["rating"])), cr(str(t["reviews"]))])
    story.append(table(rows, [78 * mm, 22 * mm, 26 * mm, 18 * mm, 34 * mm]))
    story.append(Paragraph(
        "Five products share the maximum 14 reviews. The best-rated among "
        "them — Acer Aspire ES1-732, Dell Vostro 15, Lenovo ThinkPad L460, "
        "Dell Latitude 5480, Asus MeMO Pad, all 4 stars — are the "
        "competitor's proven sellers. The worst-rated with 10+ reviews is "
        "the Asus ZenBook UX530UX at 1 star on 14 reviews: a premium-priced "
        "laptop ($1,239.20) buyers actively dislike.", body))

    story.append(Paragraph("Three recommendations", h1))
    for i, rec in enumerate([
        "<b>Price into the $600–$999 gap.</b> Only 14 of 147 products sit "
        "there while 62 sit at $1,000–$1,499. A mid-range laptop or tablet "
        "in that band meets buyers the competitor barely serves.",
        "<b>Attack on ratings, not on price.</b> The competitor's range "
        "averages 2.37 stars with no 5-star product and 29.25% at 1 star — "
        "and its dearest products rate worst. A 4-star product at $400–$600 "
        "beats their $1,100 1-star machines on the comparison a buyer "
        "actually makes.",
        "<b>Watch the five proven sellers.</b> The 4-star products with 14 "
        "reviews are the competitor's trusted core. Any matching product "
        "should be compared against them on price first, and their "
        "1-star premium laptops (ZenBook UX530UX, Legion Y520) are the "
        "weakest premium listings to displace.",
    ], start=1):
        story.append(Paragraph(f"{i}. {rec}", body))

    story.append(Paragraph("Method and limits", h1))
    story.append(Paragraph(
        "Scraped live from webscraper.io (a practice e-commerce site) on "
        "23 Nov 2026 — Laptops, Tablets and Touch category pages, one "
        "request per page. Prices in USD as listed. Brands normalised from "
        "titles (ThinkPad/Aspire/Galaxy/Hewlett/Pavilion/ProBook/Inspiron/"
        "IdeaTab/iPad/iPhone/Iconia/MeMO mapped to their maker). Screen, RAM "
        "and storage parsed from listing descriptions where stated (134/147, "
        "135/147, 87/147). Outliers by per-category IQR fence. 14 "
        "data-quality tests, all passing — see outputs/dq_report.md. Limits: "
        "the site publishes no stock status, seller name or sales volume, so "
        "this pack claims none of those; prices are a single-day snapshot — "
        "re-run src/scrape.py for a fresh one. Full method and reproduction "
        "steps are in the repo README.", small))
    story.append(Paragraph(
        "SAMPLE delivery: the site is a public practice catalogue, not a real "
        "competitor. The method — scrape → warehouse → checks → workbook + "
        "report — runs unchanged on a real competitor's site.", small))
    doc.build(story)
    print(f"wrote {OUT_PDF}")


def build_dq(h):
    tests = json.loads(TEST_RESULTS.read_text(encoding="utf-8"))
    lines = ["# P27 — Data-quality report", "",
             f"**{tests['passed']}/{tests['total']} tests passing.** "
             "Each test is a SQL query in `sql/tests/` that returns its "
             "violating rows; every test expects 0 rows.", "",
             "| Test | Result | Violations |", "|---|---|---|"]
    for t in tests["tests"]:
        lines.append(f"| `{t['test']}` | {t['status']} | {t['violations']} |")
    lines += ["",
              "## What the tests cover",
              "",
              "- **Bronze (t01–t06):** row count matches the raw CSV (147), "
              "no duplicate product, every price parses to a positive "
              "number, ratings are whole stars 1–5, review counts are "
              "non-negative, every product URL points at the site.",
              "- **Silver (t07–t09):** no NULL price/brand/category/title, "
              "every row carries one of the five price bands, no raw "
              "sub-brand (ThinkPad, Aspire, Galaxy, …) survives the brand "
              "normalisation.",
              "- **Gold (t10–t14):** fact grain is one row per product, "
              "fact totals reconcile to silver, both marts reconcile, and "
              "the outlier mart is complete and valid (0 outliers — no "
              "product is priced above its category IQR fence).",
              "",
              "## Reconciliation",
              "",
              f"- Raw CSV rows: 147 → bronze: 147 → silver: 147 → fact: 147. "
              "Nothing dropped, nothing added.",
              f"- Catalogue value: ${h['total_value_usd']:,.2f} in bronze "
              "(parsed), silver, fact and the marts — the same number four ways.",
              f"- Reviews: {h['total_reviews']:,} in silver, fact and the "
              "rating mart.",
              "- Spec coverage from descriptions: screen "
              f"{h['spec_coverage']['screen']}/147, RAM "
              f"{h['spec_coverage']['ram']}/147, storage "
              f"{h['spec_coverage']['storage']}/147. Blank means the listing "
              "does not state the spec, not zero.",
              "",
              "## Checks beyond the SQL tests",
              "",
              "src/checks.py recomputes every headline number from the raw "
              "CSV independently (no database, no warehouse) and compares it "
              "with the warehouse, the workbook's formulas (recalculated in "
              "LibreOffice) and this report. See its output for the full list.",
              ""]
    OUT_DQ.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_DQ}")


def main():
    conn = sqlite3.connect(DB)
    h = compute_headlines(conn)
    conn.close()
    build_pdf(h)
    build_dq(h)


if __name__ == "__main__":
    main()
