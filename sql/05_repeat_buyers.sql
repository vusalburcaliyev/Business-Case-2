WITH buyer_orders AS (
  SELECT period, buyer_id, COUNT(*) AS orders
  FROM quarter_orders
  WHERE sold = 1 AND buyer_id IS NOT NULL
  GROUP BY period, buyer_id
)
SELECT period, COUNT(*) AS buyers, SUM(orders >= 2) AS repeat_buyers,
       SUM(orders) AS orders_with_buyer,
       ROUND(100.0 * SUM(orders >= 2) / COUNT(*), 2) AS repeat_pct
FROM buyer_orders GROUP BY period ORDER BY period;
