"""Create small, static README previews from the same SQL outputs as the report."""
import html
from pathlib import Path


def txt(x, y, value, size=15, fill="#183346", weight=500):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}">{html.escape(str(value))}</text>')


def render(path, title, subtitle, cards, chart_title, bars, tint="#197f71"):
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 338" role="img" '
        'font-family="system-ui, sans-serif">',
        f'<title>{html.escape(title)}</title>',
        '<rect x="1" y="1" width="918" height="336" rx="16" fill="#f4f8f8" stroke="#d6e1e5"/>',
        '<path d="M17 1 H903 Q919 1 919 17 V90 H1 V17 Q1 1 17 1" fill="#102c3b"/>',
        txt(24, 29, "RETAIL QUARTER REVIEW   /   Q2 2018", 12, "#9cddd0", 750),
        txt(24, 60, title, 27, "#ffffff", 750),
        txt(25, 79, subtitle, 12, "#d6e8eb"),
    ]
    for i, (key, value) in enumerate(cards):
        x = 22 + i * 295
        parts += [
            f'<rect x="{x}" y="105" width="285" height="60" rx="9" fill="#ffffff" stroke="#d6e1e5"/>',
            txt(x + 11, 127, key, 12, "#4c6573", 650),
            txt(x + 11, 151, value, 22, weight=750),
        ]
    parts.append(txt(24, 192, chart_title, 15, weight=750))
    max_value = max(value for _, value, _ in bars)
    for i, (name, value, detail) in enumerate(bars):
        y = 215 + 34 * i
        parts += [
            txt(24, y + 9, name, 13),
            f'<rect x="238" y="{y}" width="453" height="10" rx="5" fill="#e3edee"/>',
            f'<rect x="238" y="{y}" width="{453 * value / max_value:.2f}" height="10" rx="5" fill="{tint}"/>',
            txt(707, y + 9, detail, 13, weight=700),
        ]
    parts += [txt(24, 321, "Source: Olist Brazilian E-Commerce Public Dataset · CC BY-NC-SA 4.0", 11, "#4c6573"), "</svg>"]
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def make(root: Path, outputs):
    q2 = next(row for row in outputs["01_scorecard"] if row["period"] == "2018-Q2")
    months = [r for r in outputs["02_monthly_trend"] if r["month"] in ("2018-04", "2018-05", "2018-06")]
    states = [r for r in outputs["04_state_delivery"] if r["period"] == "2018-Q2"]
    render(root / "assets/sales.svg", "Sales & customers", "Delivered orders grouped by purchase date",
           [("Merchandise sales", f"R$ {q2['sales_cents'] / 100:,.0f}"),
            ("Delivered orders with items", f"{q2['sold_orders']:,}"),
            ("Average order value", f"R$ {q2['aov_cents'] / 100:,.2f}")],
           "Delivered merchandise sales by month",
           [(label, row["sales_cents"], f"R$ {row['sales_cents'] / 100:,.0f}")
            for label, row in zip(("April", "May", "June"), months)])
    render(root / "assets/delivery.svg", "Delivery & assortment", "Rates and counts answer different questions",
           [("On-time delivery", f"{q2['on_time_pct']:.2f}%"),
            ("Late deliveries", f"{q2['measured_deliveries'] - q2['on_time_deliveries']:,}"),
            ("Cancellation rate", f"{q2['cancellation_pct']:.2f}%")],
           "Highest late delivery rates (states with at least 100 measured deliveries)",
           [(r["state"], r["late_pct"], f"{r['late_pct']:.2f}% · {r['late_deliveries']:,} late")
            for r in states[:3]], tint="#ae632b")
