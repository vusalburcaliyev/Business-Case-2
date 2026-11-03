WITH category_totals AS (
  SELECT period, category, SUM(price_cents) AS sales_cents,
         COUNT(*) AS items_sold, COUNT(DISTINCT order_id) AS orders_with_category
  FROM item_detail WHERE period IN ('2017-Q2', '2018-Q1', '2018-Q2')
  GROUP BY period, category
)
SELECT *, DENSE_RANK() OVER (PARTITION BY period ORDER BY sales_cents DESC) AS sales_rank,
       ROUND(100.0 * sales_cents / SUM(sales_cents) OVER (PARTITION BY period), 2)
         AS sales_share_pct
FROM category_totals ORDER BY period, sales_rank, category;
