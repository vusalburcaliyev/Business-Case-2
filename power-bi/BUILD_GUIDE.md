# How I mapped the report to Power BI

I kept the order scorecard and category sales at different grains. That lets the order cards count baskets once and the category chart show only the merchandise assigned to each category.

1. Run `python scripts/build.py path/to/brazilian-ecommerce.zip --export-bi`.
2. Import `data/Orders.csv` and `data/DeliveredItems.csv` in Power BI Desktop. Keep order and buyer IDs as text, `purchase_date` as Date, and the cents, item count, `sold`, and `days_vs_promise` fields as Whole Number. Keep empty days as blank.
3. Join `Orders[order_id]` (one) to `DeliveredItems[order_id]` (many), with a single filter direction from Orders to DeliveredItems. Use `Orders[period]` for a single-select quarter slicer. The category axis filters the item table only; keep category as a breakdown on its own chart.
4. Add the measures in [measures.dax](measures.dax) one at a time. Format BRL measures as currency and rates as percentages.

| Page | What I would show | Why |
|---|---|---|
| Sales & customers | Merchandise sales, orders, AOV, items per order, repeat buyers, and a sales chart by purchase month | Separates order volume from spend and adds customer context. |
| Delivery & assortment | Cancellation and on-time rates, late deliveries by state, and category sales | Puts sales next to service quality. Use `Measured Deliveries ≥ 100` on the state ranking and show the late count alongside the rate. |

```dax
Average Order Value BRL =
DIVIDE([Merchandise Sales BRL], [Delivered Orders With Items])
```

I divided the selected quarter's total merchandise sales by its delivered order count. Averaging state-level AOVs would give a low-volume state the same weight as a large one. `DIVIDE` returns blank when there are no eligible orders.

```dax
On-time Delivery Rate =
DIVIDE([On-time Deliveries], [Measured Deliveries])
```

I used measured deliveries as the denominator so missing dates do not automatically count as late. The numerator explicitly excludes blanks because DAX can compare a blank as zero.

For Q2 2018, I expect **R$ 2,807,156.64** merchandise sales, **19,646** delivered orders with items, **R$ 142.89** AOV, and **95.83%** on-time delivery. The [SQL scorecard](../results/01_scorecard.csv) and [repeat buyer output](../results/05_repeat_buyers.csv) give the reference values. The browser report is included and has been checked against SQL. This guide and DAX are supplied for a Desktop rebuild; a PBIX is not included and the DAX has not been run in Desktop.
