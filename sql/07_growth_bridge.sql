WITH quarter AS (
  SELECT period, COUNT(*) AS sold_orders, SUM(merchandise_cents) AS sales_cents
  FROM quarter_orders WHERE sold = 1 GROUP BY period
), comparison AS (
  SELECT n.sales_cents - p.sales_cents AS change_cents,
         (n.sold_orders - p.sold_orders) * (1.0 * p.sales_cents / p.sold_orders)
           AS volume_effect_cents,
         n.sold_orders * (1.0 * n.sales_cents / n.sold_orders
                           - 1.0 * p.sales_cents / p.sold_orders) AS aov_effect_cents
  FROM quarter p CROSS JOIN quarter n WHERE p.period = '2018-Q1' AND n.period = '2018-Q2'
)
SELECT change_cents, ROUND(volume_effect_cents) AS volume_effect_cents,
       ROUND(aov_effect_cents) AS aov_effect_cents FROM comparison;
