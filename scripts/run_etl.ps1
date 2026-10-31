Write-Host ">>> [1/3] Generating Raw Datasets..." -ForegroundColor Cyan
python src/data_generator.py

Write-Host ">>> [2/3] Executing Star Schema Batch Ingestion..." -ForegroundColor Cyan
python src/etl_pipeline.py

Write-Host ">>> [3/3] Running Automated Data Quality Reconciliation..." -ForegroundColor Cyan
python src/data_quality.py