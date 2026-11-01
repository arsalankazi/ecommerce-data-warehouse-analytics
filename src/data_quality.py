import sys
from sqlalchemy import text
from tabulate import tabulate
from db_engine import get_engine

def run_quality_audits():
    try:
        engine = get_engine()
    except Exception as e:
        print(f">>> [FATAL] Database connection failed: {e}")
        return 1

    print("=" * 65)
    print(">>> STARTING DATA WAREHOUSE INTEGRITY & RECONCILIATION AUDIT")
    print("=" * 65)
    
    audits = [
        {
            "name": "Check Orphan Records in Fact (Foreign Key Integrity)",
            "query": """
                SELECT COUNT(*) FROM fact_order_items f
                LEFT JOIN dim_customers c ON f.customer_key = c.customer_key
                LEFT JOIN dim_products p ON f.product_key = p.product_key
                LEFT JOIN dim_dates d ON f.date_id = d.date_id
                WHERE c.customer_key IS NULL OR p.product_key IS NULL OR d.date_id IS NULL;
            """,
            "expected": 0
        },
        {
            "name": "Check Null Values in Business-Critical Fact Columns",
            "query": """
                SELECT COUNT(*) FROM fact_order_items
                WHERE total_amount IS NULL OR quantity IS NULL OR customer_key IS NULL;
            """,
            "expected": 0
        },
        {
            "name": "Check Logical Constraint (Quantity > 0)",
            "query": "SELECT COUNT(*) FROM fact_order_items WHERE quantity <= 0;",
            "expected": 0
        },
        {
            "name": "Duplicate Primary Keys Check (fact_order_items)",
            "query": """
                SELECT COUNT(*) FROM (
                    SELECT order_item_id FROM fact_order_items 
                    GROUP BY order_item_id HAVING COUNT(*) > 1
                ) dupes;
            """,
            "expected": 0
        }
    ]

    results = []
    all_passed = True

    try:
        with engine.connect() as conn:
            for audit in audits:
                val = conn.execute(text(audit["query"])).scalar()
                passed = (val == audit["expected"])
                if not passed:
                    all_passed = False
                results.append([
                    audit["name"],
                    val,
                    audit["expected"],
                    "PASSED" if passed else "FAILED"
                ])
    except Exception as err:
        print(f">>> [ERROR] Quality audit execution query failed: {err}")
        return 1

    print(tabulate(results, headers=["Audit Check", "Found", "Expected", "Status"], tablefmt="grid"))
    
    if all_passed:
        print("\n>>> ALL DATA QUALITY AUDITS PASSED WITH ZERO RECONCILIATION ERRORS!")
        return 0
    else:
        print("\n>>> CRITICAL: ONE OR MORE QUALITY CHECKS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(run_quality_audits())
