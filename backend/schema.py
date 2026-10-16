
"""
Database schema and business rules for SQL generation.

This file contains database knowledge only:
- table name
- column names
- data types
- business meanings
- date rules
- transaction formulas
"""

TABLE_NAME = "collection_data26_sample"

TABLE_SCHEMA = {
    "table_name": TABLE_NAME,
    "columns": {
        "Merchant": {
            "type": "text",
            "description": "Merchant/business name"
        },
        "Transaction ID": {
            "type": "bigint",
            "description": "Unique transaction identifier"
        },
        "Merchant ID": {
            "type": "integer",
            "description": "Unique merchant identifier"
        },
        "Integration ID": {
            "type": "text",
            "description": "Integration reference ID"
        },
        "Amount": {
            "type": "numeric",
            "description": "Transaction amount. Use numeric/decimal precision for calculations."
        },
        "Mobile No": {
            "type": "text",
            "description": "Customer mobile number"
        },
        "Status": {
            "type": "text",
            "description": "Transaction status",
            "allowed_values": ["Success", "Failed", "Pending", "Cancelled"]
        },
        "Operator ID": {
            "type": "text",
            "description": "Operator or channel identifier"
        },
        "Product": {
            "type": "text",
            "description": "Product name if available"
        },
        "Created Date": {
            "type": "timestamp",
            "description": "Main transaction creation timestamp. Always use this for date filters."
        },
        "Updated Date": {
            "type": "timestamp",
            "description": "Transaction update timestamp. Use only if user explicitly asks for update date."
        },
        "UserKey": {
            "type": "text",
            "description": "Customer/user reference key"
        }
    }
}


BUSINESS_RULES = """
BUSINESS RULES

1. Main table:
collection_data26_sample

2. Main date column:
"Created Date"

3. Date format:
YYYY-MM-DD HH24:MI:SS

Example:
2026-06-05 09:25:19

4. Use "Created Date" for all date filters unless the user explicitly asks for "Updated Date".

5. Every query must have a date filter using "Created Date", unless the user explicitly asks for a full-table query.

6. Transaction count:
Use COUNT(*)

7. Total amount:
Use ROUND(SUM("Amount")::numeric, 2)

8. Average amount:
Use ROUND(AVG("Amount")::numeric, 2)

9. Successful transactions:
"Status" = 'Success'

10. Failed transactions:
"Status" = 'Failed'

11. Pending transactions:
"Status" = 'Pending'

12. Cancelled transactions:
"Status" = 'Cancelled'

13. Total Txn Initiated:
COUNT(*) over all statuses:
Success + Failed + Pending + Cancelled

14. Failed at SIMPAISA:
Pending + Cancelled

15. Sent to Operator:
Success + Failed

16. Success at Operator:
Success

17. Failed at Operator:
Failed

18. Processing SR (%):
Success / (Success + Failed) * 100

19. End-to-End SR (%):
Success / (Success + Failed + Pending + Cancelled) * 100

20. Use NULLIF to avoid division by zero.

21. Round all percentage results to 2 decimals.

22. Merchant-wise analysis:
GROUP BY "Merchant"

23. Merchant ID-wise analysis:
GROUP BY "Merchant ID"

24. Operator-wise analysis:
GROUP BY "Operator ID"

25. Status-wise analysis:
GROUP BY "Status"

26. For detailed row outputs, always use LIMIT 1000.

27. Prefer aggregation over raw row output.
"""


DATE_RULES = """
DATE RULES

1. Always use "Created Date" for date filtering.

2. Never use "Updated Date" unless explicitly requested.

3. Never use LIKE on date columns.

4. Never use BETWEEN for month filters.

5. Use half-open date ranges:
"Created Date" >= start_datetime
AND "Created Date" < next_period_start_datetime

6. Monthly filter example for June 2026:

WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00'

7. Daily filter example for 5 June 2026:

WHERE "Created Date" >= '2026-06-05 00:00:00'
AND "Created Date" <  '2026-06-06 00:00:00'

8. Yearly filter example for 2026:

WHERE "Created Date" >= '2026-01-01 00:00:00'
AND "Created Date" <  '2027-01-01 00:00:00'
"""


SQL_EXAMPLES = """
SQL EXAMPLES

1. Transaction count for June 2026:

SELECT COUNT(*) AS txn_count
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00';

2. Successful transactions for June 2026:

SELECT COUNT(*) AS successful_transactions
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00'
AND "Status" = 'Success';

3. Total amount for June 2026:

SELECT ROUND(SUM("Amount")::numeric, 2) AS total_amount
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00';

4. Processing SR for June 2026:

SELECT
    ROUND(
        COUNT(*) FILTER (WHERE "Status" = 'Success')::numeric
        / NULLIF(COUNT(*) FILTER (WHERE "Status" IN ('Success', 'Failed')), 0)
        * 100,
        2
    ) AS processing_sr
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00';

5. End-to-End SR for June 2026:

SELECT
    ROUND(
        COUNT(*) FILTER (WHERE "Status" = 'Success')::numeric
        / NULLIF(COUNT(*), 0)
        * 100,
        2
    ) AS end_to_end_sr
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00';

6. Merchant-wise transaction count for June 2026:

SELECT
    "Merchant",
    COUNT(*) AS txn_count
FROM collection_data26_sample
WHERE "Created Date" >= '2026-06-01 00:00:00'
AND "Created Date" <  '2026-07-01 00:00:00'
GROUP BY "Merchant"
ORDER BY txn_count DESC
LIMIT 1000;
"""
