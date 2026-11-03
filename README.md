# 🗄️ Enterprise E-Commerce Data Warehouse

**Kimball Star Schema • Connection-Pooled ETL • SQL Window Analytics**

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

An enterprise-grade, relational data warehouse engineered to deliver low-latency analytical aggregations on high-volume e-commerce transactions. Built around the **Kimball Dimensional Modeling methodology**, this warehouse orchestrates automated batch ingestion with resilient SQLAlchemy connection pooling, enforces strict pre-load data quality reconciliations, and models complex business KPIs through optimized PostgreSQL window functions.

---

## 📌 Executive Summary & Architecture

Modern data warehousing requires strict boundaries between operational ingestion, secure credential lifecycle, and analytical processing. This system eliminates data integrity risks, connection exhaustion, and query bottlenecks through:

1. **Dimensional Modeling:** Strict Star Schema design segregating transactional facts (`fact_order_items`) from analytical entity context (`dim_customers`, `dim_products`, `dim_dates`).
2. **Resilient Connection Pooling:** SQLAlchemy `QueuePool` configuration that manages persistent connections and burst traffic with automatic liveness checks (`pool_pre_ping`).
3. **Automated Quality Audits:** Pre-consumption gatekeeper audits verifying foreign key integrity, non-null guarantees, domain validity, and primary key collision prevention.
4. **Statistical SQL Intelligence:** Advanced window queries calculating dynamic customer segmentation (RFM Quintiles via `NTILE`) and financial velocity (Month-over-Month growth and rolling averages via `LAG`).

```mermaid
%%{init: {'themeVariables': {'edgeLabelBackground': '#0d3c61', 'textColor': '#ffffff'}, 'flowchart': {'nodeSpacing': 40, 'rankSpacing': 40}}}%%
flowchart TD
    subgraph Sources ["1. Operational Source Data"]
        RAW["Raw Operational CSVs<br/>(Customers, Products, Transactions)"]
    end

    subgraph IngestionEngine ["2. Python / SQLAlchemy Batch Ingestion"]
        POOL["QueuePool Engine<br/>(Pool: 10, Overflow: 20, Recycle: 1800s)"]
        TRANSFORM["Surrogate Key Resolution<br/>& Chunked Ingestion (1000/chunk)"]
        POOL --> TRANSFORM
    end

    subgraph StarSchema ["3. Kimball Star Schema (PostgreSQL 15)"]
        DIM_D["dim_dates<br/>(Calendar Granularity)"]
        DIM_C["dim_customers<br/>(Demographics & Profiles)"]
        DIM_P["dim_products<br/>(Pricing & Margins)"]
        FACT["fact_order_items<br/>(Grain: One record per line item)"]

        DIM_D --- FACT
        DIM_C --- FACT
        DIM_P --- FACT
    end

    subgraph Downstream ["4. Verification & Analytics"]
        QA["Automated Reconciliation Audits<br/>(0 Orphans, 0 Nulls, 0 PK Duplicates)"]
        ANALYTICS["Downstream SQL Window Intelligence<br/>(RFM Quintiles via NTILE & MoM via LAG)"]
    end

    RAW --> POOL
    TRANSFORM --> DIM_D
    TRANSFORM --> DIM_C
    TRANSFORM --> DIM_P
    TRANSFORM --> FACT
    FACT --> QA
    FACT --> ANALYTICS

    classDef ingestion fill:#2d1b4e,stroke:#9c27b0,stroke-width:2px,color:#ffffff;
    classDef compute fill:#0d3c61,stroke:#0288d1,stroke-width:2px,color:#ffffff;
    classDef fact fill:#4a2600,stroke:#f57c00,stroke-width:2px,color:#ffffff;
    classDef audit fill:#0d2e13,stroke:#388e3c,stroke-width:2px,color:#ffffff;

    class RAW ingestion;
    class POOL,TRANSFORM,DIM_D,DIM_C,DIM_P compute;
    class FACT fact;
    class QA,ANALYTICS audit;

    style Sources fill:#1a1a2e,stroke:#9c27b0,stroke-width:1px,color:#ffffff
    style IngestionEngine fill:#0a1f33,stroke:#0288d1,stroke-width:1px,color:#ffffff
    style StarSchema fill:#2b1c00,stroke:#f57c00,stroke-width:1px,color:#ffffff
    style Downstream fill:#0d2318,stroke:#388e3c,stroke-width:1px,color:#ffffff
```

---

## 🔒 Security & Secrets Management (Twelve-Factor Standards)

The project adheres to Twelve-Factor application principles to prevent credential leakage and ensure reproducible local deployments:

- **Environment-Driven Configuration:** All database credentials (`DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME`) are decoupled from application code and read dynamically from `.env` with sanitized local defaults.
- **Special Character URL Encoding:** Uses `urllib.parse.quote_plus` on database usernames and passwords to prevent connection string parsing attacks or connection dropouts.
- **Strict Repository Hygiene:** `.gitignore` excludes active secrets (`.env`, `*.env`), runtime database volumes (`pgdata/`), generated datasets (`data/*.csv`), and Python bytecode.
- **Network Isolation:** PostgreSQL port bindings in `docker-compose.yml` are restricted to local loopback (`127.0.0.1:5433:5432`) rather than public broadcast interfaces.

---

## 📐 Kimball Star Schema Design

The dimensional model is structured at the grain of **one row per individual transaction line item**.

```mermaid
erDiagram
    dim_dates ||--o{ fact_order_items : "date_id"
    dim_customers ||--o{ fact_order_items : "customer_key"
    dim_products ||--o{ fact_order_items : "product_key"

    dim_dates {
        int date_id PK "Format: YYYYMMDD"
        date full_date UK
        string day_of_week
        int day_num_in_month
        string month_name
        int month_num
        int quarter
        int year
        boolean is_weekend
    }

    dim_customers {
        int customer_key PK "Serial Surrogate Key"
        string customer_id UK
        string customer_name
        string email
        string city
        string state
        date signup_date
    }

    dim_products {
        int product_key PK "Serial Surrogate Key"
        string product_id UK
        string product_name
        string category
        numeric unit_cost
        numeric retail_price
    }

    fact_order_items {
        string order_item_id PK
        string order_id
        int customer_key FK
        int product_key FK
        int date_id FK
        int quantity "CHECK > 0"
        numeric unit_price
        numeric discount_amount
        numeric tax_amount
        numeric total_amount
        numeric profit
        string payment_method
        string order_status
    }
```

---

## ⚡ Engineering Implementation Details

### 1. Connection-Pooled Database Engine (`src/db_engine.py`)

To prevent connection leaks and starvation during intensive batch insertions, the engine implements SQLAlchemy's `QueuePool`:

```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,             # Persistent active connection pool
    max_overflow=20,          # Handles unexpected ingestion traffic bursts
    pool_timeout=30,          # Fail-safe timeout to prevent hanging threads
    pool_pre_ping=True,       # Active health check: verifies connection liveness
    pool_recycle=1800         # Recycles connections every 30m to prevent stale sockets
)
```

### 2. Idempotent Full-Refresh Ingestion & Key Resolution (`src/etl_pipeline.py`)

- **Idempotency via TRUNCATE + Reload:** Every pipeline run begins by executing `TRUNCATE TABLE ... CASCADE` on all dimension and fact tables before reloading. This guarantees safe reruns — a rerun can never produce duplicate `order_item_id` values, and each execution produces an identical warehouse state. For production-scale incremental loads, this will migrate to `INSERT ... ON CONFLICT (order_item_id) DO UPDATE` (tracked in Future Improvements).
- **Surrogate Key Resolution:** Replaces raw operational identifiers (`customer_id`, `product_id`) with clean integer surrogate keys (`customer_key`, `product_key`) inside memory buffers before committing records.
- **Chunked Batch Loading:** Utilizes `to_sql(..., method='multi', chunksize=1000)` to execute multi-value batched SQL statements, cutting down network round-trips to the PostgreSQL cluster.

### 3. Automated Post-Load Data Quality Gatekeeper (`src/data_quality.py`)

After the ETL batch finishes loading, an automated reconciliation suite evaluates four business rules (FK integrity, nulls, quantity > 0, PK duplicates). If any check fails, execution aborts with exit code `1`.

---

## 📊 Live Telemetry & Verification

The pipeline has been validated end-to-end against a synthetic 6,256-transaction dataset (generated via Faker) on containerized PostgreSQL 15 infrastructure.

### 1. Data Quality Audit Telemetry

```text
=================================================================
>>> STARTING DATA WAREHOUSE INTEGRITY & RECONCILIATION AUDIT
=================================================================
+------------------------------------------------------+---------+------------+----------+
| Audit Check                                          |   Found |   Expected | Status   |
+======================================================+=========+============+==========+
| Check Orphan Records in Fact (Foreign Key Integrity) |       0 |          0 | PASSED   |
+------------------------------------------------------+---------+------------+----------+
| Check Null Values in Business-Critical Fact Columns  |       0 |          0 | PASSED   |
+------------------------------------------------------+---------+------------+----------+
| Check Logical Constraint (Quantity > 0)              |       0 |          0 | PASSED   |
+------------------------------------------------------+---------+------------+----------+
| Duplicate Primary Keys Check (fact_order_items)      |       0 |          0 | PASSED   |
+------------------------------------------------------+---------+------------+----------+

>>> ALL DATA QUALITY AUDITS PASSED WITH ZERO RECONCILIATION ERRORS!
```

### 2. Advanced SQL Window Analytics Output

#### A. RFM Customer Segmentation (`NTILE(5)` Statistical Windowing)

Segments the customer base into 5 statistical quintiles across Recency, Frequency, and Monetary attributes to isolate VIP champions from churn-risk cohorts.

**The query (`sql/analytics_kpis.sql`):**

```sql
WITH customer_aggregations AS (
    SELECT
        c.customer_id,
        c.customer_name,
        MAX(d.full_date)                    AS last_order_date,
        COUNT(DISTINCT f.order_id)          AS total_orders,
        ROUND(SUM(f.total_amount), 2)       AS monetary_value
    FROM fact_order_items f
    JOIN dim_customers c ON f.customer_key = c.customer_key
    JOIN dim_dates    d ON f.date_id      = d.date_id
    WHERE f.order_status = 'Completed'
    GROUP BY c.customer_id, c.customer_name
),
rfm_scores AS (
    SELECT
        customer_id, customer_name, last_order_date, total_orders, monetary_value,
        NTILE(5) OVER (ORDER BY last_order_date)  AS r_score,
        NTILE(5) OVER (ORDER BY total_orders)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary_value)   AS m_score
    FROM customer_aggregations
)
SELECT
    customer_id, customer_name, total_orders, monetary_value,
    (r_score + f_score + m_score) AS composite_rfm_score,
    CASE
        WHEN (r_score + f_score + m_score) >= 12 THEN 'VIP Champions'
        WHEN (r_score + f_score + m_score) >= 9  THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 6  THEN 'Potential Churn Risk'
        ELSE 'Hibernating / Lost'
    END AS customer_segment
FROM rfm_scores
ORDER BY composite_rfm_score DESC, monetary_value DESC
LIMIT 10;
```

**Live output on the 6,256-row dataset:**

```text
+---------------+--------------------+----------------+------------------+-------------+---------------+
| customer_id   | customer_name      |   total_orders |   monetary_value |   rfm_score | segment       |
+===============+====================+================+==================+=============+===============+
| CUST_0159     | Emily Long         |             18 |          16696.4 |          15 | VIP Champions |
| CUST_0078     | Evelyn Garcia      |             16 |          10686.0 |          15 | VIP Champions |
| CUST_0071     | Jennifer Robertson |             13 |           9308.9 |          15 | VIP Champions |
| CUST_0110     | Renee Jones        |             13 |          15108.1 |          14 | VIP Champions |
| CUST_0130     | Lisa Henderson     |             11 |          13732.0 |          14 | VIP Champions |
+---------------+--------------------+----------------+------------------+-------------+---------------+
```

#### B. Month-over-Month (MoM) Growth & 3-Month Moving Average (`LAG()`)

Calculates Month-over-Month revenue growth using `LAG()`, and calculates the 3-month moving average using `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`.

**The query (`sql/analytics_kpis.sql`):**

```sql
WITH monthly_revenue AS (
    SELECT
        d.year, d.month_num, d.month_name,
        ROUND(SUM(f.total_amount), 2)  AS current_month_revenue,
        COUNT(DISTINCT f.order_id)     AS total_orders
    FROM fact_order_items f
    JOIN dim_dates d ON f.date_id = d.date_id
    WHERE f.order_status IN ('Completed', 'Shipped')
    GROUP BY d.year, d.month_num, d.month_name
)
SELECT
    year, month_name, current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num) AS previous_month_revenue,
    ROUND(
        (current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num))
        / NULLIF(LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num), 0) * 100, 2
    ) AS mom_growth_pct,
    ROUND(
        AVG(current_month_revenue) OVER (
            ORDER BY year, month_num ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_3_month_avg_revenue
FROM monthly_revenue
ORDER BY year, month_num;
```

**Live output on the 6,256-row dataset:**

```text
+--------+--------------+-------------------------+------------------+------------------+-------------------+
|   year | month_name   |   current_month_revenue |   prev_month_rev |   mom_growth_pct |   rolling_3mo_avg |
+========+==============+=========================+==================+==================+===================+
|   2025 | November     |                  134812 |              nan |              nan |            134812 |
|   2025 | December     |                  150016 |           134812 |            11.28 |            142414 |
|   2026 | January      |                  130785 |           150016 |           -12.82 |            138538 |
|   2026 | February     |                  113154 |           130785 |           -13.48 |            131318 |
|   2026 | March        |                  180094 |           113154 |            59.16 |            141344 |
|   2026 | April        |                  108005 |           180094 |           -40.03 |            133751 |
+--------+--------------+-------------------------+------------------+------------------+-------------------+
```

---

## 🗂️ Repository Structure

```text
ecommerce-data-warehouse-analytics/
├── .env.example                    # Sanitized environment template for public version control
├── .gitignore                      # Exclusion rules for secrets, DB data, logs, and datasets
├── docker-compose.yml              # Dedicated PostgreSQL container configuration
├── requirements.txt                # Version-constrained Python dependencies
├── README.md                       # Architecture documentation & telemetry metrics
├── data/                           # Local operational data storage (excluded from VCS)
├── sql/
│   ├── ddl_schema.sql              # DDL defining Star Schema, tables, and B-tree indexes
│   └── analytics_kpis.sql          # Production analytical window queries
├── src/
│   ├── db_engine.py                # SQLAlchemy QueuePool connection manager
│   ├── data_generator.py           # Controlled mock transaction generator (Faker)
│   ├── etl_pipeline.py             # Surrogate key resolution & chunked loading logic
│   ├── data_quality.py             # Automated reconciliation & integrity test suite
│   └── run_analytics.py            # SQL window execution script
└── scripts/
    ├── setup_db.ps1                # Container provisioning & schema setup
    └── run_etl.ps1                 # Batch ETL orchestration pipeline
```

---

## 🛠️ Tech Stack & Tooling

- **Data Warehouse Engine:** PostgreSQL 15 (Docker containerized)
- **Data Modeling:** Ralph Kimball Star Schema Methodology (Surrogate Keys, Fact Tables, Dimension Tables)
- **Programming & Libraries:** Python 3.10+, SQLAlchemy 2.0 (`QueuePool`), `psycopg2-binary`, Pandas, Faker, Tabulate
- **Infrastructure & Automation:** Docker Compose, PowerShell (Windows-native orchestration scripts)

---

## 🚦 Getting Started

### Prerequisites

- Docker Desktop installed and running.
- Python 3.10+ installed.
- **Hardware:** 2GB+ RAM (for PostgreSQL 15 container), ~500MB free disk space.

### Execution Instructions

**1. Clone the repository:**

```bash
git clone https://github.com/arsalankazi/ecommerce-data-warehouse-analytics.git
cd ecommerce-data-warehouse-analytics
```

**2. Initialize Python Environment & Secrets:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create local environment config from sanitized template
Copy-Item .env.example .env
```

**3. Spin up Infrastructure & Initialize DDL:**

```powershell
.\scripts\setup_db.ps1
```

**4. Execute ETL Batch Pipeline & Quality Audits:**

```powershell
.\scripts\run_etl.ps1
```

**5. Run Window Analytics Queries:**

```powershell
python src\run_analytics.py
```

---

## 🚀 Future Improvements

- **Incremental Loading:** Migrate from full-refresh `TRUNCATE + reload` to incremental ingestion using `WHERE updated_at > last_load_ts` and `INSERT ... ON CONFLICT (order_item_id) DO UPDATE` — eliminating redundant reloads on large warehouses.
- **SCD Type 2:** Add slowly changing dimension logic to `dim_customers` (with `valid_from` / `valid_to` / `is_current` columns) to track historical address and email changes.
- **CI/CD Pipeline:** GitHub Actions workflow to run pytest unit tests and the `data_quality.py` audit suite on every push and pull request.
- **Cross-Platform Orchestration:** Provide Bash equivalents (`setup_db.sh`, `run_etl.sh`) for Linux / macOS contributors.
- **Workflow Orchestration:** Migrate from PowerShell wrapper scripts to Airflow or Prefect for scheduling, retries, and observability.
- **Testing:** Add pytest unit tests for surrogate key resolution and ETL transformation logic (`data_quality.py` currently covers post-load validation, not unit tests).

---

## 👨‍💻 Author & Maintainer

<p align="left">
  <img src="https://github.com/arsalankazi.png" width="90" style="border-radius:50%;" alt="Arsalan Kazi" />
</p>

### **Kazi Arsalan Ajaj Ahmed**
*Data Engineer | Big Data & Cloud*

[![GitHub](https://img.shields.io/badge/GitHub-Profile-181717?style=for-the-badge&logo=github)](https://github.com/arsalankazi)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/arsalankazi)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail)](mailto:kaziarsalan810@gmail.com)

---

### 🎯 Core Engineering Focus

- **Dimensional Modeling:** Kimball Star Schema, Surrogate Key Strategies, Fact Granularity & SCD Types.
- **Pipeline Engineering:** Resilient Connection-Pooled Batch Ingestion, Idempotent Workflows & Automated Reconciliation.
- **Analytical SQL:** Multi-table Joins, CTE Orchestration, and Statistical Window Aggregations (`NTILE`, `LAG`, Rolling Metrics).