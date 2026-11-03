# Source and reproducibility

**Olist and collaborators.** *Brazilian E-Commerce Public Dataset by Olist*. [Kaggle data card](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The source is licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

This noncommercial portfolio includes aggregated results and charts adapted from the dataset; those derived data outputs are shared under CC BY-NC-SA 4.0. The original archive and order- and buyer-level outputs are not committed. Transformations include cleaning, joining, filtering to the selected periods and statuses, translating category labels, aggregating and charting.

I used the orders, customers, order items, products, and category translation CSVs. The downloaded archive's SHA-256 was `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`. Kaggle may repackage the download; the build validates the fields, keys, and reported totals rather than requiring that exact ZIP checksum.

From the repository root, run:

```bash
python scripts/build.py path/to/brazilian-ecommerce.zip
```

I used Python 3.11+ and SQLite 3.25+ (Python's `sqlite3` module reports the linked SQLite version). No Python packages are required. Add `--export-bi` to generate the two Power BI input CSVs under `data/`. The build creates a local SQLite database, writes the query CSVs and audit, and rebuilds both dashboard views and the previews. It checks that categories, months, and quarters reconcile and that joins leave one row per order.
