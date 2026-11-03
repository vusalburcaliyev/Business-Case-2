"""Rebuild the SQLite model, published results, and offline report from the Olist zip."""
import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"
RESULTS = ROOT / "results"
DATA = ROOT / "data"
DASHBOARD = ROOT / "dashboard"


def cents(value):
    amount = Decimal(value) * 100
    if not amount.is_finite() or amount != amount.to_integral_value():
        raise ValueError(f"Expected a monetary amount to cent precision: {value}")
    return int(amount)


def stamp(value):
    return datetime.fromisoformat(value).isoformat(sep=" ") if value else None


def rows(archive, name):
    with io.TextIOWrapper(archive.open(name), encoding="utf-8-sig", newline="") as source:
        yield from csv.DictReader(source)


def load(db, archive):
    schema, model = (SQL / "00_model.sql").read_text().split("-- Aggregate items", 1)
    db.executescript(schema)
    feeds = [
        ("orders", "olist_orders_dataset.csv", 6, lambda r: (
            r["order_id"].strip(), r["customer_id"].strip(), r["order_status"].strip().lower(),
            stamp(r["order_purchase_timestamp"]), stamp(r["order_delivered_customer_date"]),
            stamp(r["order_estimated_delivery_date"]))),
        ("customers", "olist_customers_dataset.csv", 3, lambda r: (
            r["customer_id"].strip(), r["customer_unique_id"].strip() or None,
            r["customer_state"].strip().upper() or None)),
        ("order_items", "olist_order_items_dataset.csv", 5, lambda r: (
            r["order_id"].strip(), int(r["order_item_id"]), r["product_id"].strip(),
            cents(r["price"]), cents(r["freight_value"]))),
        ("products", "olist_products_dataset.csv", 2, lambda r: (
            r["product_id"].strip(), r["product_category_name"].strip() or None)),
        ("translations", "product_category_name_translation.csv", 2, lambda r: (
            r["product_category_name"].strip(), r["product_category_name_english"].strip())),
    ]
    audit = Counter()
    with zipfile.ZipFile(archive) as z, db:
        for table, filename, width, parse in feeds:
            seen = {}
            insert = []
            for row in rows(z, filename):
                audit[f"source_{table}"] += 1
                values = parse(row)
                key = values[:2] if table == "order_items" else values[0]
                if not key or (table == "order_items" and (not key[0] or key[1] < 1)):
                    raise ValueError(f"Missing key in {table}")
                if key in seen:
                    if values != seen[key]:
                        raise ValueError(f"Conflicting duplicate key in {table}")
                    audit[f"exact_duplicates_{table}"] += 1
                    continue
                seen[key] = values
                insert.append(values)
            db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * width)})", insert)
            audit[f"loaded_{table}"] = len(insert)
            audit.setdefault(f"exact_duplicates_{table}", 0)
    db.executescript("-- Aggregate items" + model)
    for metric, query in {
        "order_customer_unmatched": "SELECT COUNT(*) FROM order_fact WHERE buyer_id IS NULL",
        "item_order_unmatched": "SELECT COUNT(*) FROM order_items i LEFT JOIN orders o USING(order_id) WHERE o.order_id IS NULL",
        "item_product_unmatched": "SELECT COUNT(*) FROM order_items i LEFT JOIN products p USING(product_id) WHERE p.product_id IS NULL",
        "unknown_status": """SELECT COUNT(*) FROM orders WHERE status NOT IN
           ('approved','canceled','created','delivered','invoiced','processing','shipped','unavailable')""",
        "placed_orders_without_items": "SELECT COUNT(*) FROM order_fact WHERE items = 0",
        "delivered_orders_without_items": "SELECT COUNT(*) FROM order_fact WHERE status = 'delivered' AND items = 0",
        "delivered_orders_missing_or_invalid_dates": "SELECT COUNT(*) FROM order_fact WHERE status = 'delivered' AND days_vs_promise IS NULL",
        "sold_lines_uncategorized": "SELECT COUNT(*) FROM item_detail WHERE category = 'uncategorized'",
        "sold_lines_with_untranslated_category": """SELECT COUNT(*) FROM order_items i
          JOIN order_fact f USING(order_id) JOIN products p USING(product_id)
          LEFT JOIN translations t USING(category_code)
          WHERE f.sold = 1 AND p.category_code IS NOT NULL AND t.category_code IS NULL""",
    }.items():
        audit[metric] = db.execute(query).fetchone()[0]
    for required in ("order_customer_unmatched", "item_order_unmatched", "item_product_unmatched", "unknown_status"):
        if audit[required]:
            raise ValueError(f"Unexpected source change: {required} = {audit[required]}")
    return audit


def save_csv(path, header, records):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(records)


def table(db, query, path):
    cursor = db.execute(query)
    records = cursor.fetchall()
    header = [col[0] for col in cursor.description]
    save_csv(path, header, records)
    return [dict(zip(header, row)) for row in records]


def check(db, audit, result):
    order_count, distinct_count = db.execute("SELECT COUNT(*), COUNT(DISTINCT order_id) FROM order_fact").fetchone()
    assert order_count == distinct_count == audit["loaded_orders"], "Join changed order grain"
    m = result["02_monthly_trend"]
    assert len(m) == 18 and all(m[i]["month"] > m[i - 1]["month"] for i in range(1, 18)), "Missing month in LAG"
    for row in result["01_scorecard"]:
        quarter = row["period"]
        month_set = {quarter[:4] + suffix for suffix in (
            ("-01", "-02", "-03") if quarter.endswith("Q1") else ("-04", "-05", "-06"))}
        assert sum(x["sales_cents"] for x in m if x["month"] in month_set) == row["sales_cents"]
        cats = [x for x in result["03_category_rank"] if x["period"] == quarter]
        assert sum(x["sales_cents"] for x in cats) == row["sales_cents"], "Category sales do not reconcile"
        assert sum(x["items_sold"] for x in cats) == row["items_sold"], "Category item count does not reconcile"
        assert row["on_time_deliveries"] <= row["measured_deliveries"] <= row["delivered_orders"] <= row["placed_orders"]
        assert row["sold_orders"] <= row["delivered_orders"]
    b = result["07_growth_bridge"][0]
    assert abs(b["change_cents"] - b["volume_effect_cents"] - b["aov_effect_cents"]) <= 1
    assert sum(x["change_cents"] for x in result["08_category_change"]) == b["change_cents"]
    for x in result["06_order_value_sensitivity"]:
        assert 0 < x["above_threshold_orders"] < x["sold_orders"]
        assert x["sales_without_high_value_cents"] < x["sales_cents"]
    print("Passed: order grain, calendar coverage, category/quarter totals, delivery denominators, and growth bridge.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="The Olist ZIP downloaded from Kaggle")
    parser.add_argument("--export-bi", action="store_true", help="Also write fact CSVs under data/")
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DATA) as tmp:
        db_path = Path(tmp) / "olist.sqlite"
        db = sqlite3.connect(db_path)
        try:
            audit = load(db, args.archive)
            result = {
                path.stem: table(db, path.read_text(encoding="utf-8"), RESULTS / f"{path.stem}.csv")
                for path in sorted(SQL.glob("[0-9][0-9]_*.sql")) if not path.name.startswith("00")
            }
            check(db, audit, result)
            if args.export_bi:
                table(db, "SELECT * FROM order_fact ORDER BY order_id", DATA / "Orders.csv")
                table(db, "SELECT * FROM item_detail ORDER BY order_id, category, price_cents, freight_cents", DATA / "DeliveredItems.csv")
        finally:
            db.close()
        db_path.replace(DATA / "olist.sqlite")
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template = DASHBOARD / "template.html"
    if template.exists():
        from previews import make

        payload = json.dumps(result, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
        (ROOT / "Retail_Dashboard.html").write_text(
            template.read_text(encoding="utf-8").replace("/* @RESULTS */", payload),
            encoding="utf-8",
        )
        make(ROOT, result)
    print(f"Built {len(result)} SQL outputs from {audit['loaded_orders']:,} orders and {audit['loaded_order_items']:,} items.")


if __name__ == "__main__":
    main()
