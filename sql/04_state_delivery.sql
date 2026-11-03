WITH state_totals AS (
  SELECT period, state, COUNT(*) AS placed_orders,
         SUM(CASE WHEN sold = 1 THEN merchandise_cents ELSE 0 END) AS sales_cents,
         COUNT(days_vs_promise) AS measured_deliveries,
         SUM(CASE WHEN days_vs_promise > 0 THEN 1 ELSE 0 END) AS late_deliveries
  FROM quarter_orders GROUP BY period, state
), eligible AS (
  SELECT *, 1.0 * late_deliveries / measured_deliveries AS late_rate
  FROM state_totals WHERE measured_deliveries >= 100
)
SELECT *, ROUND(100.0 * late_rate, 2) AS late_pct,
       RANK() OVER (PARTITION BY period ORDER BY late_rate DESC) AS late_rate_rank
FROM eligible ORDER BY period, late_rate_rank, late_deliveries DESC, state;
