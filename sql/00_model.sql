CREATE TABLE orders (
  order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, status TEXT NOT NULL,
  purchased TEXT NOT NULL, delivered TEXT, promised TEXT
);
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY, buyer_id TEXT NOT NULL, state TEXT NOT NULL
);
CREATE TABLE order_items (
  order_id TEXT NOT NULL, line_no INTEGER NOT NULL, product_id TEXT NOT NULL,
  price_cents INTEGER NOT NULL CHECK (price_cents > 0),
  freight_cents INTEGER NOT NULL CHECK (freight_cents >= 0),
  PRIMARY KEY (order_id, line_no)
);
CREATE TABLE products (product_id TEXT PRIMARY KEY, category_code TEXT);
CREATE TABLE translations (category_code TEXT PRIMARY KEY, english TEXT NOT NULL);

-- Aggregate items before joining to orders, so a five-item basket counts once.
CREATE TABLE order_fact AS
WITH basket AS (
  SELECT order_id, COUNT(*) AS items, SUM(price_cents) AS merchandise_cents,
         SUM(freight_cents) AS freight_cents
  FROM order_items GROUP BY order_id
)
SELECT o.order_id, c.buyer_id, c.state, o.status,
       DATE(o.purchased) AS purchase_date, SUBSTR(o.purchased, 1, 7) AS month,
       SUBSTR(o.purchased, 1, 4) || '-Q' ||
         ((CAST(SUBSTR(o.purchased, 6, 2) AS INTEGER) - 1) / 3 + 1) AS period,
       COALESCE(b.items, 0) AS items,
       COALESCE(b.merchandise_cents, 0) AS merchandise_cents,
       COALESCE(b.freight_cents, 0) AS freight_cents,
       CASE WHEN o.status = 'delivered' AND b.items > 0 THEN 1 ELSE 0 END AS sold,
       CASE WHEN o.status = 'delivered' AND o.delivered >= o.purchased
                  AND DATE(o.promised) >= DATE(o.purchased)
            THEN CAST(JULIANDAY(DATE(o.delivered)) - JULIANDAY(DATE(o.promised)) AS INTEGER)
       END AS days_vs_promise
FROM orders o
LEFT JOIN basket b ON b.order_id = o.order_id
LEFT JOIN customers c ON c.customer_id = o.customer_id;
CREATE UNIQUE INDEX ix_fact_order ON order_fact(order_id);
CREATE INDEX ix_fact_period ON order_fact(period);
CREATE INDEX ix_fact_month ON order_fact(month);

CREATE VIEW item_detail AS
SELECT f.order_id, f.period, f.state,
       COALESCE(t.english, p.category_code, 'uncategorized') AS category,
       i.price_cents, i.freight_cents
FROM order_fact f JOIN order_items i ON i.order_id = f.order_id
LEFT JOIN products p ON p.product_id = i.product_id
LEFT JOIN translations t ON t.category_code = p.category_code
WHERE f.sold = 1;

CREATE VIEW quarter_orders AS
SELECT * FROM order_fact WHERE period IN ('2017-Q2', '2018-Q1', '2018-Q2');
