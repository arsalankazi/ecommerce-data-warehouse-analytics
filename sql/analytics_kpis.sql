-- Query 1: RFM Customer Segmentation using NTILE Window Function
WITH customer_aggregations AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        MAX(d.full_date) AS last_order_date,
        COUNT(DISTINCT f.order_id) AS total_orders,
        ROUND(SUM(f.total_amount), 2) AS monetary_value
    FROM fact_order_items f
    JOIN dim_customers c ON f.customer_key = c.customer_key
    JOIN dim_dates d ON f.date_id = d.date_id
    WHERE f.order_status = 'Completed'
    GROUP BY c.customer_id, c.customer_name
),
rfm_scores AS (
    SELECT 
        customer_id,
        customer_name,
        last_order_date,
        total_orders,
        monetary_value,
        NTILE(5) OVER (ORDER BY last_order_date) AS r_score,
        NTILE(5) OVER (ORDER BY total_orders) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_value) AS m_score
    FROM customer_aggregations
)
SELECT 
    customer_id,
    customer_name,
    total_orders,
    monetary_value,
    (r_score + f_score + m_score) AS composite_rfm_score,
    CASE 
        WHEN (r_score + f_score + m_score) >= 12 THEN 'VIP Champions'
        WHEN (r_score + f_score + m_score) >= 9 THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 6 THEN 'Potential Churn Risk'
        ELSE 'Hibernating / Lost'
    END AS customer_segment
FROM rfm_scores
ORDER BY composite_rfm_score DESC, monetary_value DESC
LIMIT 10;

-- Query 2: Month-over-Month (MoM) Growth & Moving Averages using LAG
WITH monthly_revenue AS (
    SELECT 
        d.year,
        d.month_num,
        d.month_name,
        ROUND(SUM(f.total_amount), 2) AS current_month_revenue,
        COUNT(DISTINCT f.order_id) AS total_orders
    FROM fact_order_items f
    JOIN dim_dates d ON f.date_id = d.date_id
    WHERE f.order_status IN ('Completed', 'Shipped')
    GROUP BY d.year, d.month_num, d.month_name
)
SELECT 
    year,
    month_name,
    current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num) AS previous_month_revenue,
    ROUND(
        (current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num)) 
        / NULLIF(LAG(current_month_revenue, 1) OVER (ORDER BY year, month_num), 0) * 100, 
        2
    ) AS mom_growth_pct,
    ROUND(
        AVG(current_month_revenue) OVER (
            ORDER BY year, month_num ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_3_month_avg_revenue
FROM monthly_revenue
ORDER BY year, month_num;