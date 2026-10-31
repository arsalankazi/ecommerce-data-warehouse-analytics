DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_dates CASCADE;

-- 1. Date Dimension
CREATE TABLE dim_dates (
    date_id INT PRIMARY KEY,               -- Format: YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    day_of_week VARCHAR(10) NOT NULL,
    day_num_in_month INT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    month_num INT NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- 2. Customer Dimension
CREATE TABLE dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    signup_date DATE NOT NULL
);

-- 3. Product Dimension
CREATE TABLE dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    retail_price NUMERIC(10, 2) NOT NULL
);

-- 4. Fact Order Items
CREATE TABLE fact_order_items (
    order_item_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    customer_key INT NOT NULL REFERENCES dim_customers(customer_key),
    product_key INT NOT NULL REFERENCES dim_products(product_key),
    date_id INT NOT NULL REFERENCES dim_dates(date_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_amount NUMERIC(10, 2) DEFAULT 0.00,
    tax_amount NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    profit NUMERIC(10, 2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    order_status VARCHAR(20) NOT NULL
);

CREATE INDEX idx_fact_customer_key ON fact_order_items(customer_key);
CREATE INDEX idx_fact_product_key ON fact_order_items(product_key);
CREATE INDEX idx_fact_date_id ON fact_order_items(date_id);