Write-Host ">>> [1/3] Spinning up PostgreSQL Warehouse Container..." -ForegroundColor Cyan
docker compose up -d

Write-Host ">>> Waiting 5s for Postgres initialization..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ">>> [2/3] Initializing Star Schema DDL..." -ForegroundColor Cyan
Get-Content sql/ddl_schema.sql | docker exec -i dw-postgres psql -U warehouse_user -d ecommerce_warehouse

Write-Host ">>> [3/3] PostgreSQL Warehouse is Ready!" -ForegroundColor Green