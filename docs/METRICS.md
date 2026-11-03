# What I counted

Every quarter is assigned by **purchase date**, even if the delivery occurred in a later quarter. Q2 2018 is April 1 to June 30; Q1 2018 is January 1 to March 31; Q2 2017 is the year-over-year comparison. The monthly series uses January 2017 through June 2018.

| KPI | Definition | Why I used it |
|---|---|---|
| Orders placed | All distinct order IDs in the purchase period, regardless of current status | Measures how many orders entered the process. |
| Delivered orders with items | Orders marked delivered and linked to at least one item row | Aligns the sales numerator with the order denominator. |
| Delivered merchandise sales | Sum of item prices for those orders, in BRL | Measures the value of delivered merchandise before any unobserved returns or refunds. Freight is separate. |
| Average order value (AOV) | Delivered merchandise sales ÷ delivered orders with items | Shows how much merchandise value each delivered order contributes, on average. |
| Items per order | Delivered item rows ÷ delivered orders with items | Helps distinguish a larger basket from a more expensive one. One numbered item row represents one item. |
| Cancellation rate | Orders with status `canceled` ÷ all placed orders | Preserves the size of the ordering funnel. `unavailable` is reported separately. |
| On-time delivery rate | Deliveries arriving by the promised calendar date ÷ delivered orders with usable actual and promised dates | A delivery on the promised date counts as on time. I removed missing or inconsistent dates from this denominator only. |
| Repeat buyer rate | Buyers with at least two delivered orders with items in the quarter ÷ buyers with at least one | Uses the stable buyer ID. It measures repeat buying inside a quarter, not cohort retention or first-ever purchase. |
| Category sales share | Delivered item value in the category ÷ all delivered merchandise sales | Shows how much the category contributes. An order can include more than one category. |

## Where the totals came from

| Table | One row represents | Join key |
|---|---|---|
| Orders | An order and its status and dates | `order_id` |
| Customers | An order's customer record; `customer_unique_id` identifies a buyer across orders | `customer_id` |
| Order items | An individual numbered item on an order | `order_id` + `order_item_id` |
| Products | A product and its category code | `product_id` |
| Category translation | A category code and English name | Category code |

I parsed the timestamps, standardized state and status labels, and converted BRL values to integer cents before summing. I checked each source key for duplicate rows and stopped the build if a key had conflicting values. I kept orders with no item rows in the placed-order denominator. When a product category had no translation, I kept its original code; when it had no category, I kept it as **Uncategorized**. That kept sales in the total. The [audit](../results/audit.json) shows what the checks found.

I kept legitimate high-value orders in the primary scorecard. I calculated the pooled 99th-percentile order value for Q1 and Q2 2018, then recomputed sales after excluding orders strictly above that same threshold in both quarters. That is a separate sensitivity check, so one quarter cannot appear better simply because it got a different cutoff.

The dataset is a historical snapshot. It does not identify returns, refunds, discounts, or cost of goods. I did not use the payment totals as merchandise sales, and I did not estimate net revenue, profit, or inventory KPIs from missing inputs. Seller or carrier causes cannot be inferred from the state ranking.
