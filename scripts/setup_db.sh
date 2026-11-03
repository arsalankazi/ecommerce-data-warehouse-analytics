#!/bin/bash
set -e

echo -e "\033[0;36m>>> [1/3] Spinning up PostgreSQL Warehouse Container...\033[0m"
docker compose up -d

echo -e "\033[0;33m>>> Waiting 5s for Postgres initialization...\033[0m"
sleep 5

echo -e "\033[0;36m>>> [2/3] Initializing Star Schema DDL...\033[0m"
cat ../sql/ddl_schema.sql | docker exec -i dw-postgres psql -U warehouse_user -d ecommerce_warehouse

echo -e "\033[0;32m>>> [3/3] PostgreSQL Warehouse is Ready!\033[0m"