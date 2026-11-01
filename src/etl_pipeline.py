import os
import pandas as pd
from sqlalchemy import text
from db_engine import get_engine

# Decoupled Data Directory with Environment Fallback
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_DIR = os.getenv("WAREHOUSE_DATA_DIR", DEFAULT_DATA_DIR)

def populate_date_dimension(engine, start_date="2025-01-01", end_date="2027-12-31"):
    print(">>> [ETL] Populating dim_dates calendar table...")
    dates = pd.date_range(start=start_date, end=end_date)
    df_dates = pd.DataFrame({
        "full_date": dates.date,
        "date_id": dates.strftime("%Y%m%d").astype(int),
        "day_of_week": dates.strftime("%A"),
        "day_num_in_month": dates.day,
        "month_name": dates.strftime("%B"),
        "month_num": dates.month,
        "quarter": dates.quarter,
        "year": dates.year,
        "is_weekend": dates.day_of_week >= 5
    })
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dim_dates CASCADE;"))
    
    df_dates.to_sql("dim_dates", con=engine, if_exists="append", index=False, method="multi", chunksize=1000)
    print(f">>> [ETL] Loaded {len(df_dates)} rows into dim_dates.")

def run_etl():
    engine = get_engine()
    
    # 1. Date Dimension
    populate_date_dimension(engine)
    
    # 2. Customer Dimension
    print(">>> [ETL] Loading dim_customers...")
    cust_file = os.path.join(DATA_DIR, "raw_customers.csv")
    df_cust = pd.read_csv(cust_file)
    df_cust["signup_date"] = pd.to_datetime(df_cust["signup_date"]).dt.date
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dim_customers CASCADE;"))
    df_cust.to_sql("dim_customers", con=engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f">>> [ETL] Loaded {len(df_cust)} rows into dim_customers.")

    # 3. Product Dimension
    print(">>> [ETL] Loading dim_products...")
    prod_file = os.path.join(DATA_DIR, "raw_products.csv")
    df_prod = pd.read_csv(prod_file)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dim_products CASCADE;"))
    df_prod.to_sql("dim_products", con=engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f">>> [ETL] Loaded {len(df_prod)} rows into dim_products.")

    # 4. Fact Table Ingestion with Surrogate Key Lookup
    print(">>> [ETL] Transforming and resolving keys for fact_order_items...")
    orders_file = os.path.join(DATA_DIR, "raw_orders.csv")
    df_orders = pd.read_csv(orders_file)
    initial_orders_count = len(df_orders)
    
    with engine.connect() as conn:
        cust_map = pd.read_sql("SELECT customer_key, customer_id FROM dim_customers", conn)
        prod_map = pd.read_sql("SELECT product_key, product_id FROM dim_products", conn)

    df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
    df_orders["date_id"] = df_orders["order_date"].dt.strftime("%Y%m%d").astype(int)

    # Surrogate Key Joins
    df_fact = df_orders.merge(cust_map, on="customer_id", how="inner")
    df_fact = df_fact.merge(prod_map, on="product_id", how="inner")
    
    resolved_count = len(df_fact)
    if resolved_count < initial_orders_count:
        dropped = initial_orders_count - resolved_count
        print(f">>> [WARN] {dropped} unmapped records dropped during surrogate key resolution.")

    cols_to_keep = [
        "order_item_id", "order_id", "customer_key", "product_key", "date_id",
        "quantity", "unit_price", "discount_amount", "tax_amount", "total_amount",
        "profit", "payment_method", "order_status"
    ]
    df_fact = df_fact[cols_to_keep]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_order_items;"))

    print(f">>> [ETL] Loading {len(df_fact)} records into fact_order_items using connection pooling...")
    df_fact.to_sql(
        "fact_order_items",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )
    print(">>> [ETL] Star Schema ETL execution complete!")

if __name__ == "__main__":
    run_etl()
