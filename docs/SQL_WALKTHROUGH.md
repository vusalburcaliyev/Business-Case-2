# How I used SQL

I built two views of the same sales: one row per order for the scorecard, and one row per delivered item for categories. Mixing those grains would count a three-item basket three times. The [model](../sql/00_model.sql) aggregates item values before joining to orders; the category view keeps the item rows.

| Query | What I wanted to answer | Why I wrote it this way |
|---|---|---|
| [01 · Scorecard](../sql/01_scorecard.sql) | Did sales, orders, basket size, and fulfillment move together? | Conditional sums let each KPI use the right set of orders. `NULLIF` leaves a rate blank when there is no denominator. |
| [02 · Monthly trend](../sql/02_monthly_trend.sql) | Is a month up from the month before, or from the same month last year? | I used `LAG` after grouping by month. One row back is the prior month; 12 rows back is the same month last year. I checked the calendar had no gaps. |
| [03 · Category rank](../sql/03_category_rank.sql) | Which categories sold the most in each quarter? | `DENSE_RANK` restarts per quarter. A tie gets the same rank without leaving a gap before the next category. The share uses a separate window sum over the whole quarter. |
| [04 · State delivery](../sql/04_state_delivery.sql) | Where were orders most likely to arrive late, and how many did that affect? | I removed groups with fewer than 100 measured deliveries before ranking. `RANK` compares the unrounded rates; equal rates share a place and leave a gap. I kept the late count alongside the rate. |
| [05 · Repeat buyers](../sql/05_repeat_buyers.sql) | How many buyers came back in the same quarter? | I grouped by stable buyer ID first. The order-specific customer ID would make a returning buyer look like someone new. |
| [06 · Order value sensitivity](../sql/06_order_value_sensitivity.sql) | Would the sales comparison change without the highest-value orders? | `ROW_NUMBER` finds the pooled 99th-percentile position. Both quarters use the same threshold; orders tied at the threshold stay in the comparison. |
| [07 · Growth bridge](../sql/07_growth_bridge.sql) | How much of the change is explained by order count vs. order value? | I priced the volume change at Q1 AOV and applied the AOV change to Q2 volume. The two parts add back to the observed change. This is arithmetic, not evidence of why shoppers spent more. |
| [08 · Category change](../sql/08_category_change.sql) | Which categories contributed most to the change from Q1 to Q2? | I put both quarters into columns with conditional sums. The category changes add up to the overall change. |

## A closer look at the category ranking

```sql
WITH category_totals AS (
  SELECT period, category, SUM(price_cents) AS sales_cents
  FROM item_detail
  GROUP BY period, category
)
SELECT period, category, sales_cents,
       DENSE_RANK() OVER (
         PARTITION BY period ORDER BY sales_cents DESC
       ) AS sales_rank
FROM category_totals;
```

I grouped by category before ranking so the window sees one total per category, not individual items. I did not put the category name inside the window's `ORDER BY`: that would break a real tie. The [complete query](../sql/03_category_rank.sql) adds sales share, item count, and a stable display order. If two categories tie for second, `DENSE_RANK` produces 1, 2, 2, 3; `RANK` produces 1, 2, 2, 4.

## A closer look at the delivery ranking

```sql
SELECT period, state, measured_deliveries, late_deliveries,
       RANK() OVER (
         PARTITION BY period ORDER BY late_rate DESC
       ) AS late_rate_rank
FROM eligible;
```

I ranked after filtering out states below the volume threshold. A state with 1 late delivery out of 2 would otherwise outrank most larger states. I rounded the percentage only for display, so two distinct rates do not tie just because their labels look the same.
