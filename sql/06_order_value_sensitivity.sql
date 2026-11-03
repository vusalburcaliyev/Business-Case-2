-- Use one p99 cutoff for both quarters and keep all orders at the cutoff.
WITH ranked AS (
  SELECT merchandise_cents,
         ROW_NUMBER() OVER (ORDER BY merchandise_cents, order_id) AS position,
         COUNT(*) OVER () AS n
  FROM quarter_orders WHERE sold = 1 AND period IN ('2018-Q1', '2018-Q2')
), cutoff AS (
  SELECT merchandise_cents AS threshold_cents FROM ranked
  WHERE position = (99 * n + 99) / 100
)
SELECT period, threshold_cents, COUNT(*) AS sold_orders,
       SUM(q.merchandise_cents) AS sales_cents,
       SUM(q.merchandise_cents > threshold_cents) AS above_threshold_orders,
       SUM(CASE WHEN q.merchandise_cents <= threshold_cents THEN q.merchandise_cents ELSE 0 END)
         AS sales_without_high_value_cents
FROM cutoff CROSS JOIN quarter_orders q
WHERE sold = 1 AND period IN ('2018-Q1', '2018-Q2')
GROUP BY period, threshold_cents ORDER BY period;
