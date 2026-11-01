import os
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# Decoupled Data Directory with Environment Fallback
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_DIR = os.getenv("WAREHOUSE_DATA_DIR", DEFAULT_DATA_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

def generate_mock_dataset(
    num_customers=int(os.getenv("GEN_NUM_CUSTOMERS", 200)),
    num_products=int(os.getenv("GEN_NUM_PRODUCTS", 50)),
    num_orders=int(os.getenv("GEN_NUM_ORDERS", 2500))
):
    print(">>> Generating raw e-commerce operational datasets...")

    # 1. Customers
    customers = []
    for i in range(1, num_customers + 1):
        c_id = f"CUST_{i:04d}"
        customers.append({
            "customer_id": c_id,
            "customer_name": fake.name(),
            "email": fake.unique.email(),
            "city": fake.city(),
            "state": fake.state(),
            "signup_date": fake.date_between(start_date="-2y", end_date="today")
        })
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(os.path.join(DATA_DIR, "raw_customers.csv"), index=False)

    # 2. Products
    categories = {
        "Electronics": (50.0, 800.0),
        "Clothing": (10.0, 150.0),
        "Home & Kitchen": (15.0, 300.0),
        "Books": (5.0, 60.0),
        "Footwear": (25.0, 200.0)
    }
    products = []
    for i in range(1, num_products + 1):
        p_id = f"PROD_{i:04d}"
        cat = random.choice(list(categories.keys()))
        min_p, max_p = categories[cat]
        retail_price = round(random.uniform(min_p, max_p), 2)
        unit_cost = round(retail_price * random.uniform(0.5, 0.75), 2)
        products.append({
            "product_id": p_id,
            "product_name": f"{cat} Item {i}",
            "category": cat,
            "unit_cost": unit_cost,
            "retail_price": retail_price
        })
    df_products = pd.DataFrame(products)
    df_products.to_csv(os.path.join(DATA_DIR, "raw_products.csv"), index=False)

    # 3. Orders & Line Items
    order_items = []
    start_date = datetime.now() - timedelta(days=365)
    item_counter = 1

    for o_idx in range(1, num_orders + 1):
        order_id = f"ORD_{o_idx:05d}"
        cust = random.choice(customers)
        order_date = start_date + timedelta(days=random.randint(0, 365))
        payment_method = random.choice(["Credit Card", "UPI", "Net Banking", "Debit Card"])
        order_status = random.choices(["Completed", "Shipped", "Cancelled", "Returned"], weights=[75, 15, 6, 4])[0]

        items_in_order = random.randint(1, 4)
        for _ in range(items_in_order):
            prod = random.choice(products)
            qty = random.choices([1, 2, 3, 5], weights=[60, 25, 10, 5])[0]
            price = prod["retail_price"]
            cost = prod["unit_cost"]
            discount = round(price * qty * (0.05 if random.random() < 0.3 else 0.0), 2)
            tax = round((price * qty - discount) * 0.18, 2)
            total = round((price * qty - discount) + tax, 2)
            profit = round(total - (cost * qty) - tax, 2)

            order_items.append({
                "order_item_id": f"ITEM_{item_counter:06d}",
                "order_id": order_id,
                "customer_id": cust["customer_id"],
                "product_id": prod["product_id"],
                "order_date": order_date.strftime("%Y-%m-%d"),
                "quantity": qty,
                "unit_price": price,
                "discount_amount": discount,
                "tax_amount": tax,
                "total_amount": total,
                "profit": profit,
                "payment_method": payment_method,
                "order_status": order_status
            })
            item_counter += 1

    df_orders = pd.DataFrame(order_items)
    df_orders.to_csv(os.path.join(DATA_DIR, "raw_orders.csv"), index=False)
    print(f">>> Successfully generated {len(df_customers)} customers, {len(df_products)} products, and {len(df_orders)} order item transactions!")

if __name__ == "__main__":
    generate_mock_dataset()
