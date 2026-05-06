# sqlslice

Lightweight query profiler that breaks down slow SQL into stage-by-stage timing reports.

---

## Installation

```bash
pip install sqlslice
```

---

## Usage

```python
from sqlslice import QueryProfiler

profiler = QueryProfiler(dsn="postgresql://user:password@localhost/mydb")

report = profiler.profile("""
    SELECT orders.*, customers.name
    FROM orders
    JOIN customers ON orders.customer_id = customers.id
    WHERE orders.created_at > '2024-01-01'
""")

report.print_summary()
```

**Example output:**

```
Stage               Duration    % of Total
------------------  ----------  ----------
Parse & Plan        12.4ms      8%
Index Scan          45.1ms      30%
Hash Join           78.3ms      52%
Result Fetch        15.2ms      10%
------------------  ----------  ----------
Total               151.0ms     100%
```

Use `report.slowest_stage()` to quickly identify the bottleneck, or `report.to_dict()` to export results for further analysis.

---

## Features

- Stage-by-stage query timing breakdown
- Works with PostgreSQL, MySQL, and SQLite
- Minimal setup — no agents or extensions required
- Export reports as JSON or CSV

---

## License

MIT © sqlslice contributors