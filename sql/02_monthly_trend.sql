WITH monthly AS (
  SELECT month, COUNT(*) AS placed_orders, SUM(sold) AS sold_orders,
         SUM(CASE WHEN sold = 1 THEN merchandise_cents ELSE 0 END) AS sales_cents
  FROM order_fact WHERE month BETWEEN '2017-01' AND '2018-06'
  GROUP BY month
), compared AS (
  SELECT *, LAG(sales_cents) OVER (ORDER BY month) AS previous_sales_cents,
            LAG(sales_cents, 12) OVER (ORDER BY month) AS last_year_sales_cents
  FROM monthly
)
SELECT *, ROUND(100.0 * (sales_cents - previous_sales_cents)
                     / NULLIF(previous_sales_cents, 0), 2) AS mom_pct,
          ROUND(100.0 * (sales_cents - last_year_sales_cents)
                     / NULLIF(last_year_sales_cents, 0), 2) AS yoy_pct
FROM compared ORDER BY month;
