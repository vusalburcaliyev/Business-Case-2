-- Compare numerator and denominator together for each quarter.
SELECT period, COUNT(*) AS placed_orders, SUM(sold) AS sold_orders,
       SUM(CASE WHEN sold = 1 THEN merchandise_cents ELSE 0 END) AS sales_cents,
       SUM(CASE WHEN sold = 1 THEN items ELSE 0 END) AS items_sold,
       SUM(CASE WHEN sold = 1 THEN freight_cents ELSE 0 END) AS freight_cents,
       SUM(status = 'canceled') AS canceled_orders,
       SUM(status = 'unavailable') AS unavailable_orders,
       SUM(status = 'delivered') AS delivered_orders,
       COUNT(days_vs_promise) AS measured_deliveries,
       SUM(CASE WHEN days_vs_promise <= 0 THEN 1 ELSE 0 END) AS on_time_deliveries,
       ROUND(1.0 * SUM(CASE WHEN sold = 1 THEN merchandise_cents ELSE 0 END)
             / NULLIF(SUM(sold), 0), 2) AS aov_cents,
       ROUND(1.0 * SUM(CASE WHEN sold = 1 THEN items ELSE 0 END)
             / NULLIF(SUM(sold), 0), 3) AS items_per_order,
       ROUND(100.0 * SUM(status = 'canceled') / COUNT(*), 2) AS cancellation_pct,
       ROUND(100.0 * SUM(CASE WHEN days_vs_promise <= 0 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(days_vs_promise), 0), 2) AS on_time_pct
FROM quarter_orders
GROUP BY period
ORDER BY period;
