Write-Host ">>> [1/4] Generating Raw Datasets..." -ForegroundColor Cyan
python src/data_generator.py

Write-Host ">>> [2/4] Executing Star Schema Batch Ingestion..." -ForegroundColor Cyan
python src/etl_pipeline.py

Write-Host ">>> [3/4] Running Automated Data Quality Reconciliation..." -ForegroundColor Cyan
python src/data_quality.py

Write-Host ">>> [4/4] Verifying Fact Table Row Count (Database Check)..." -ForegroundColor Cyan
docker exec -i dw-postgres psql -U warehouse_user -d ecommerce_warehouse -c "SELECT COUNT(*) AS total_fact_rows FROM fact_order_items;"