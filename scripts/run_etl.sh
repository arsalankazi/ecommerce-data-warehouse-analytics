#!/bin/bash
set -e

echo -e "\033[0;36m>>> [1/4] Generating Raw Datasets...\033[0m"
python ../src/data_generator.py

echo -e "\033[0;36m>>> [2/4] Executing Star Schema Batch Ingestion...\033[0m"
python ../src/etl_pipeline.py

echo -e "\033[0;36m>>> [3/4] Running Automated Data Quality Reconciliation...\033[0m"
python ../src/data_quality.py

echo -e "\033[0;36m>>> [4/4] Verifying Fact Table Row Count (Database Check)...\033[0m"
docker exec -i dw-postgres psql -U warehouse_user -d ecommerce_warehouse -c "SELECT COUNT(*) AS total_fact_rows FROM fact_order_items;"