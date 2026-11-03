WITH totals AS (
  SELECT category,
         SUM(CASE WHEN period = '2018-Q1' THEN price_cents ELSE 0 END) AS q1_sales_cents,
         SUM(CASE WHEN period = '2018-Q2' THEN price_cents ELSE 0 END) AS q2_sales_cents
  FROM item_detail WHERE period IN ('2018-Q1', '2018-Q2') GROUP BY category
)
SELECT *, q2_sales_cents - q1_sales_cents AS change_cents
FROM totals ORDER BY change_cents, category;
