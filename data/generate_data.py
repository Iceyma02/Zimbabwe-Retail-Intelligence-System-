"""
ZimRetail IQ — Data Generator
Generates realistic Zimbabwean retail data across multiple retailers
Run once before starting the app: python data/generate_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sqlite3
import os

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
#  RETAILERS
# ─────────────────────────────────────────────
RETAILERS_LIST = [
    {"retailer_id": "PNP",     "name": "TM Pick n Pay",    "color": "#e31837"},
    {"retailer_id": "OK",      "name": "OK Zimbabwe",       "color": "#ff6d00"},
    {"retailer_id": "SPAR",    "name": "Spar Zimbabwe",     "color": "#007b40"},
    {"retailer_id": "SAIMART", "name": "SaiMart",           "color": "#1565c0"},
    {"retailer_id": "CHOPPIES","name": "Choppies Zimbabwe", "color": "#f9a825"},
]

# ─────────────────────────────────────────────
#  STORES — Real locations across Zimbabwe
# ─────────────────────────────────────────────
STORES = [
    # TM Pick n Pay
    {"store_id": "S001", "retailer_id": "PNP", "name": "TM PnP Sam Levy's",    "city": "Harare",        "suburb": "Borrowdale",   "lat": -17.7523, "lng": 31.0982, "size_sqm": 3200, "opened_year": 2004, "manager": "Tatenda Moyo"},
    {"store_id": "S002", "retailer_id": "PNP", "name": "TM PnP Westgate",      "city": "Harare",        "suburb": "Westgate",     "lat": -17.7833, "lng": 30.9833, "size_sqm": 2800, "opened_year": 2008, "manager": "Rudo Chikwanda"},
    {"store_id": "S003", "retailer_id": "PNP", "name": "TM PnP Avondale",      "city": "Harare",        "suburb": "Avondale",     "lat": -17.7957, "lng": 31.0333, "size_sqm": 1900, "opened_year": 2010, "manager": "Blessing Ncube"},
    # OK Zimbabwe
    {"store_id": "S004", "retailer_id": "OK",  "name": "OK Mart Eastgate",     "city": "Harare",        "suburb": "Eastgate",     "lat": -17.8292, "lng": 31.0522, "size_sqm": 2100, "opened_year": 2006, "manager": "Farai Mutasa"},
    {"store_id": "S005", "retailer_id": "OK",  "name": "OK Bulawayo Centre",   "city": "Bulawayo",      "suburb": "City Centre",  "lat": -20.1500, "lng": 28.5833, "size_sqm": 2600, "opened_year": 2003, "manager": "Nomsa Dlamini"},
    {"store_id": "S006", "retailer_id": "OK",  "name": "OK Mutare Branch",     "city": "Mutare",        "suburb": "Central",      "lat": -18.9707, "lng": 32.6709, "size_sqm": 1700, "opened_year": 2009, "manager": "Tendai Chimombe"},
    # Spar Zimbabwe
    {"store_id": "S007", "retailer_id": "SPAR","name": "Spar Borrowdale",      "city": "Harare",        "suburb": "Borrowdale",   "lat": -17.7401, "lng": 31.1012, "size_sqm": 2500, "opened_year": 2012, "manager": "Simba Dube"},
    {"store_id": "S008", "retailer_id": "SPAR","name": "Spar Gweru",           "city": "Gweru",         "suburb": "Central",      "lat": -19.4500, "lng": 29.8167, "size_sqm": 1500, "opened_year": 2011, "manager": "Memory Sibanda"},
    # SaiMart
    {"store_id": "S009", "retailer_id": "SAIMART","name": "SaiMart Harare CBD","city": "Harare",        "suburb": "CBD",          "lat": -17.8292, "lng": 31.0500, "size_sqm": 2200, "opened_year": 2023, "manager": "Prosper Nyoni"},
    {"store_id": "S010", "retailer_id": "SAIMART","name": "SaiMart Bulawayo",  "city": "Bulawayo",      "suburb": "Nkulumane",    "lat": -20.1650, "lng": 28.5620, "size_sqm": 1800, "opened_year": 2023, "manager": "Grace Mpofu"},
    # Choppies
    {"store_id": "S011", "retailer_id": "CHOPPIES","name": "Choppies Masvingo","city": "Masvingo",      "suburb": "Central",      "lat": -20.0722, "lng": 30.8322, "size_sqm": 1600, "opened_year": 2015, "manager": "Tapiwa Sithole"},
    {"store_id": "S012", "retailer_id": "CHOPPIES","name": "Choppies Vic Falls","city": "Victoria Falls","suburb": "Town Centre",  "lat": -17.9243, "lng": 25.8572, "size_sqm": 1200, "opened_year": 2016, "manager": "Prosperity Moyo"},
]

# ─────────────────────────────────────────────
#  PRODUCTS — Zimbabwean brands
# ─────────────────────────────────────────────
PRODUCTS = [
    {"product_id": "P001", "name": "Fresh Full Cream Milk 2L",      "category": "Dairy",       "brand": "Dendairy",      "unit_price": 2.80, "unit_cost": 1.90, "shelf_life_days": 7,   "reorder_point": 50,  "reorder_qty": 200},
    {"product_id": "P002", "name": "Lacto Yoghurt 500g",            "category": "Dairy",       "brand": "Dendairy",      "unit_price": 1.50, "unit_cost": 0.95, "shelf_life_days": 14,  "reorder_point": 40,  "reorder_qty": 150},
    {"product_id": "P003", "name": "Kefalos Cheddar 400g",          "category": "Dairy",       "brand": "Kefalos",       "unit_price": 4.20, "unit_cost": 2.80, "shelf_life_days": 30,  "reorder_point": 25,  "reorder_qty": 100},
    {"product_id": "P004", "name": "Olivine Cooking Oil 2L",        "category": "Cooking",     "brand": "Olivine",       "unit_price": 4.50, "unit_cost": 3.10, "shelf_life_days": 365, "reorder_point": 80,  "reorder_qty": 300},
    {"product_id": "P005", "name": "Gloria Flour 2kg",              "category": "Cooking",     "brand": "National Foods","unit_price": 2.20, "unit_cost": 1.40, "shelf_life_days": 180, "reorder_point": 100, "reorder_qty": 400},
    {"product_id": "P006", "name": "Blue Ribbon Sugar 2kg",         "category": "Cooking",     "brand": "Tongaat Hulett","unit_price": 2.60, "unit_cost": 1.70, "shelf_life_days": 730, "reorder_point": 90,  "reorder_qty": 350},
    {"product_id": "P007", "name": "Coca-Cola 2L",                  "category": "Beverages",   "brand": "Coca-Cola",     "unit_price": 2.00, "unit_cost": 1.30, "shelf_life_days": 180, "reorder_point": 120, "reorder_qty": 500},
    {"product_id": "P008", "name": "Mazoe Orange Crush 2L",         "category": "Beverages",   "brand": "Schweppes ZW",  "unit_price": 3.20, "unit_cost": 2.10, "shelf_life_days": 365, "reorder_point": 60,  "reorder_qty": 250},
    {"product_id": "P009", "name": "Tanganda Tea Bags 100pk",       "category": "Beverages",   "brand": "Tanganda",      "unit_price": 3.50, "unit_cost": 2.20, "shelf_life_days": 730, "reorder_point": 40,  "reorder_qty": 150},
    {"product_id": "P010", "name": "Lobels White Bread 700g",       "category": "Bakery",      "brand": "Lobels",        "unit_price": 1.20, "unit_cost": 0.75, "shelf_life_days": 5,   "reorder_point": 80,  "reorder_qty": 300},
    {"product_id": "P011", "name": "Bakers Inn Brown Bread 700g",   "category": "Bakery",      "brand": "Bakers Inn",    "unit_price": 1.30, "unit_cost": 0.80, "shelf_life_days": 5,   "reorder_point": 70,  "reorder_qty": 280},
    {"product_id": "P012", "name": "Gold Seal Roller Meal 10kg",    "category": "Staples",     "brand": "National Foods","unit_price": 7.50, "unit_cost": 5.20, "shelf_life_days": 180, "reorder_point": 60,  "reorder_qty": 200},
    {"product_id": "P013", "name": "Uji Refined Mealie Meal 5kg",   "category": "Staples",     "brand": "Uji",           "unit_price": 4.50, "unit_cost": 3.00, "shelf_life_days": 180, "reorder_point": 55,  "reorder_qty": 180},
    {"product_id": "P014", "name": "Vaseline Body Lotion 400ml",    "category": "Personal Care","brand": "Unilever",      "unit_price": 3.80, "unit_cost": 2.40, "shelf_life_days": 730, "reorder_point": 30,  "reorder_qty": 120},
    {"product_id": "P015", "name": "Sunlight Dish Soap 750ml",      "category": "Household",   "brand": "Unilever",      "unit_price": 2.10, "unit_cost": 1.30, "shelf_life_days": 730, "reorder_point": 50,  "reorder_qty": 200},
    {"product_id": "P016", "name": "Colcom Polony 500g",            "category": "Meat",        "brand": "Colcom",        "unit_price": 3.20, "unit_cost": 2.10, "shelf_life_days": 10,  "reorder_point": 40,  "reorder_qty": 150},
    {"product_id": "P017", "name": "Pro Sausages 500g",             "category": "Meat",        "brand": "Colcom",        "unit_price": 3.50, "unit_cost": 2.30, "shelf_life_days": 10,  "reorder_point": 35,  "reorder_qty": 140},
    {"product_id": "P018", "name": "Willards Cheese Curls 120g",    "category": "Snacks",      "brand": "Willards",      "unit_price": 1.20, "unit_cost": 0.70, "shelf_life_days": 90,  "reorder_point": 60,  "reorder_qty": 240},
    {"product_id": "P019", "name": "Simba Chips 120g",              "category": "Snacks",      "brand": "Simba",         "unit_price": 1.10, "unit_cost": 0.65, "shelf_life_days": 90,  "reorder_point": 60,  "reorder_qty": 240},
    {"product_id": "P020", "name": "Tastic Rice 2kg",               "category": "Staples",     "brand": "Tastic",        "unit_price": 3.80, "unit_cost": 2.50, "shelf_life_days": 730, "reorder_point": 70,  "reorder_qty": 250},
]

SUPPLIERS = [
    {"supplier_id": "SUP001", "name": "Dendairy",           "lead_time_days": 2,  "reliability_score": 88, "payment_terms_days": 30},
    {"supplier_id": "SUP002", "name": "National Foods",     "lead_time_days": 3,  "reliability_score": 82, "payment_terms_days": 45},
    {"supplier_id": "SUP003", "name": "Olivine Industries", "lead_time_days": 4,  "reliability_score": 79, "payment_terms_days": 30},
    {"supplier_id": "SUP004", "name": "Coca-Cola Zimbabwe", "lead_time_days": 2,  "reliability_score": 95, "payment_terms_days": 14},
    {"supplier_id": "SUP005", "name": "Schweppes Zimbabwe", "lead_time_days": 3,  "reliability_score": 91, "payment_terms_days": 21},
    {"supplier_id": "SUP006", "name": "Lobels Bread",       "lead_time_days": 1,  "reliability_score": 85, "payment_terms_days": 7},
    {"supplier_id": "SUP007", "name": "Bakers Inn",         "lead_time_days": 1,  "reliability_score": 83, "payment_terms_days": 7},
    {"supplier_id": "SUP008", "name": "Colcom Foods",       "lead_time_days": 2,  "reliability_score": 87, "payment_terms_days": 14},
    {"supplier_id": "SUP009", "name": "Unilever Zimbabwe",  "lead_time_days": 5,  "reliability_score": 93, "payment_terms_days": 30},
    {"supplier_id": "SUP010", "name": "Tanganda Tea",       "lead_time_days": 4,  "reliability_score": 90, "payment_terms_days": 30},
    {"supplier_id": "SUP011", "name": "Tongaat Hulett",     "lead_time_days": 5,  "reliability_score": 76, "payment_terms_days": 45},
    {"supplier_id": "SUP012", "name": "Willards Foods",     "lead_time_days": 4,  "reliability_score": 84, "payment_terms_days": 30},
    {"supplier_id": "SUP013", "name": "Kefalos Dairy",      "lead_time_days": 3,  "reliability_score": 80, "payment_terms_days": 21},
    {"supplier_id": "SUP014", "name": "Tastic Rice SA",     "lead_time_days": 7,  "reliability_score": 88, "payment_terms_days": 60},
]


def generate_sales_data():
    records = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=540)
    store_multipliers = {"S001":1.6,"S002":1.3,"S003":0.9,"S004":1.0,"S005":1.1,
                         "S006":0.7,"S007":1.2,"S008":0.6,"S009":1.0,"S010":0.8,
                         "S011":0.65,"S012":0.4}
    seasonal = {12:1.5,1:1.3,4:1.2,8:1.1,9:0.85,2:0.95,3:1.0,5:1.0,6:0.95,7:0.9,10:1.05,11:1.2}
    products_df = pd.DataFrame(PRODUCTS)
    current = start_date
    while current <= end_date:
        dow_mult = 1.4 if current.weekday()>=5 else (1.2 if current.weekday()==4 else 1.0)
        month_mult = seasonal.get(current.month, 1.0)
        for store in STORES:
            for _, prod in products_df.iterrows():
                base_sales = random.uniform(8, 45)
                sm = store_multipliers.get(store["store_id"], 0.8)
                noise = np.random.normal(1.0, 0.15)
                units = max(0, int(base_sales * sm * dow_mult * month_mult * noise))
                revenue = round(units * prod["unit_price"], 2)
                cost = round(units * prod["unit_cost"], 2)
                records.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "store_id": store["store_id"],
                    "retailer_id": store["retailer_id"],
                    "product_id": prod["product_id"],
                    "units_sold": units, "revenue": revenue,
                    "cost": cost, "profit": round(revenue - cost, 2)
                })
        current += timedelta(days=1)
    return pd.DataFrame(records)


def generate_inventory_data():
    records = []
    today = datetime.now()
    for store in STORES:
        for prod in PRODUCTS:
            roll = random.random()
            if roll < 0.12:
                stock = random.randint(0, int(prod["reorder_point"] * 0.4)); status = "CRITICAL"
            elif roll < 0.28:
                stock = random.randint(int(prod["reorder_point"]*0.4), prod["reorder_point"]); status = "LOW"
            elif roll < 0.55:
                stock = random.randint(prod["reorder_point"], prod["reorder_point"]*2); status = "ADEQUATE"
            else:
                stock = random.randint(prod["reorder_point"]*2, prod["reorder_point"]*4); status = "GOOD"
            expiry_days = random.randint(2, prod["shelf_life_days"])
            records.append({
                "store_id": store["store_id"], "retailer_id": store["retailer_id"],
                "product_id": prod["product_id"], "current_stock": stock,
                "reorder_point": prod["reorder_point"], "reorder_qty": prod["reorder_qty"],
                "status": status,
                "expiry_date": (today + timedelta(days=expiry_days)).strftime("%Y-%m-%d"),
                "last_restocked": (today - timedelta(days=random.randint(1,14))).strftime("%Y-%m-%d"),
                "days_until_expiry": expiry_days
            })
    return pd.DataFrame(records)


def generate_supplier_credit_data():
    records = []
    today = datetime.now()
    statuses = ["ACTIVE","ACTIVE","ACTIVE","LIMITED_CREDIT","LIMITED_CREDIT","STOPPED"]
    for sup in SUPPLIERS:
        for i in range(random.randint(1,4)):
            invoice_date = today - timedelta(days=random.randint(5,75))
            due_date = invoice_date + timedelta(days=sup["payment_terms_days"])
            amount = round(random.uniform(1200, 18000), 2)
            paid = round(amount * random.uniform(0, 0.6), 2) if random.random() > 0.4 else 0
            records.append({
                "supplier_id": sup["supplier_id"], "supplier_name": sup["name"],
                "invoice_id": f"INV-{sup['supplier_id']}-{i+1:03d}",
                "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount_usd": amount, "amount_paid": paid,
                "outstanding_usd": round(amount - paid, 2),
                "overdue_days": max(0, (today - due_date).days),
                "supplier_status": random.choice(statuses),
                "last_delivery_date": (today - timedelta(days=random.randint(1,20))).strftime("%Y-%m-%d"),
                "lead_time_days": sup["lead_time_days"], "reliability_score": sup["reliability_score"]
            })
    return pd.DataFrame(records)


def generate_staff_data():
    records = []
    for store in STORES:
        headcount = int(store["size_sqm"] / 120)
        records.append({
            "store_id": store["store_id"], "store_name": store["name"],
            "retailer_id": store["retailer_id"], "city": store["city"],
            "headcount": headcount,
            "monthly_labour_cost_usd": round(headcount * random.uniform(350, 520), 2),
            "overtime_hours_this_month": random.randint(0, 80),
            "vacancies": random.randint(0, 3),
            "avg_tenure_years": round(random.uniform(1.5, 6.5), 1)
        })
    return pd.DataFrame(records)


def generate_shrinkage_data():
    records = []
    today = datetime.now()
    causes = ["Theft","Expiry/Spoilage","Damage","Admin Error","Supplier Short Delivery"]
    for store in STORES:
        for month_offset in range(6):
            record_date = today - timedelta(days=30*month_offset)
            for cause in causes:
                records.append({
                    "store_id": store["store_id"], "store_name": store["name"],
                    "retailer_id": store["retailer_id"],
                    "month": record_date.strftime("%Y-%m"), "cause": cause,
                    "value_usd": round(random.uniform(50, 800), 2),
                    "units_lost": random.randint(5, 120)
                })
    return pd.DataFrame(records)


def generate_promotions_data():
    promo_names = ["Back to School Special","Easter Bonanza","Winter Warmers",
                   "Independence Day Sale","Christmas Mega Deal","New Year Bash",
                   "Monthly FMCG Special","Loyalty Members Week"]
    records = []
    today = datetime.now()
    for i, name in enumerate(promo_names):
        start = today - timedelta(days=random.randint(20,300))
        end = start + timedelta(days=random.randint(5,14))
        pre_rev = round(random.uniform(15000, 60000), 2)
        promo_rev = round(pre_rev * random.uniform(1.1, 1.8), 2)
        promo_cost = round(random.uniform(500, 4000), 2)
        records.append({
            "promo_id": f"PROMO-{i+1:03d}", "promo_name": name,
            "start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"),
            "pre_promo_revenue": pre_rev, "promo_revenue": promo_rev, "promo_cost_usd": promo_cost,
            "roi_percent": round(((promo_rev - pre_rev - promo_cost)/promo_cost)*100, 1),
            "status": "ACTIVE" if end >= today else "COMPLETED"
        })
    return pd.DataFrame(records)


def generate_competitor_prices():
    competitors = ["TM Pick n Pay","OK Zimbabwe","Spar Zimbabwe","SaiMart","Choppies"]
    records = []
    for prod in PRODUCTS[:12]:
        base = prod["unit_price"]
        for comp in competitors:
            variance = random.uniform(-0.25, 0.30)
            comp_price = round(base * (1 + variance), 2)
            records.append({
                "product_id": prod["product_id"], "product_name": prod["name"],
                "category": prod["category"], "base_price": base,
                "retailer": comp, "retailer_price": comp_price,
                "price_diff": round(comp_price - base, 2)
            })
    return pd.DataFrame(records)


def generate_store_costs():
    records = []
    today = datetime.now()
    for store in STORES:
        sf = store["size_sqm"] / 2000
        for mo in range(12):
            rd = today - timedelta(days=30*mo)
            records.append({
                "store_id": store["store_id"], "retailer_id": store["retailer_id"],
                "month": rd.strftime("%Y-%m"),
                "rent_usd": round(sf*random.uniform(2800,3500),2),
                "utilities_usd": round(sf*random.uniform(800,1400),2),
                "labour_usd": round(sf*random.uniform(4000,6000),2),
                "maintenance_usd": round(sf*random.uniform(200,600),2),
                "security_usd": round(sf*random.uniform(300,500),2),
                "other_usd": round(random.uniform(200,800),2)
            })
    return pd.DataFrame(records)


def generate_logistics_data():
    records = []
    today = datetime.now()
    statuses = ["ORDER_PLACED","DISPATCHED","IN_TRANSIT","AT_WAREHOUSE","DELIVERED","DELAYED"]
    for i in range(55):
        sup = random.choice(SUPPLIERS)
        store = random.choice(STORES)
        order_date = today - timedelta(days=random.randint(0,10))
        expected = order_date + timedelta(days=sup["lead_time_days"])
        status = random.choice(statuses)
        delay_days = random.randint(1,4) if status=="DELAYED" else 0
        records.append({
            "order_id": f"ORD-{i+1:04d}", "supplier_id": sup["supplier_id"],
            "supplier_name": sup["name"], "store_id": store["store_id"],
            "store_name": store["name"], "retailer_id": store["retailer_id"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "expected_delivery": expected.strftime("%Y-%m-%d"),
            "actual_delivery": (expected+timedelta(days=delay_days)).strftime("%Y-%m-%d") if status=="DELIVERED" else None,
            "status": status, "delay_days": delay_days,
            "order_value_usd": round(random.uniform(800,12000),2),
            "items_count": random.randint(2,8)
        })
    return pd.DataFrame(records)


def generate_economic_data():
    records = []
    today = datetime.now()
    zig_rate = 13.5
    for d in range(180):
        rd = today - timedelta(days=d)
        zig_rate = max(10, zig_rate + random.uniform(-0.3, 0.5))
        records.append({
            "date": rd.strftime("%Y-%m-%d"),
            "usd_zig_rate": round(zig_rate, 2),
            "fuel_price_usd_per_litre": round(random.uniform(1.42, 1.68), 3),
            "inflation_rate_percent": round(random.uniform(2.1, 8.4), 1),
            "load_shedding_hours": random.randint(0, 12),
            "forex_availability": random.choice(["HIGH","MEDIUM","LOW","CRITICAL"])
        })
    return pd.DataFrame(records)


def save_to_sqlite(db_path=None):
    if db_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "zimretail_iq.db")
    print("📊 ZimRetail IQ — Generating data...")
    os.makedirs("data", exist_ok=True)

    retailers_df = pd.DataFrame(RETAILERS_LIST)
    stores_df = pd.DataFrame(STORES)
    products_df = pd.DataFrame(PRODUCTS)
    suppliers_df = pd.DataFrame(SUPPLIERS)

    print("  ⏳ Generating 18 months of sales data...")
    sales_df = generate_sales_data()
    inventory_df = generate_inventory_data()
    credit_df = generate_supplier_credit_data()
    staff_df = generate_staff_data()
    shrinkage_df = generate_shrinkage_data()
    promotions_df = generate_promotions_data()
    competitor_df = generate_competitor_prices()
    costs_df = generate_store_costs()
    logistics_df = generate_logistics_data()
    economic_df = generate_economic_data()

    conn = sqlite3.connect(db_path)
    tables = {
        "retailers": retailers_df,
        "stores": stores_df,
        "products": products_df,
        "suppliers": suppliers_df,
        "sales": sales_df,
        "inventory": inventory_df,
        "supplier_credit": credit_df,
        "staff": staff_df,
        "shrinkage": shrinkage_df,
        "promotions": promotions_df,
        "competitor_prices": competitor_df,
        "store_costs": costs_df,
        "logistics": logistics_df,
        "economic_indicators": economic_df
    }
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        print(f"  ✅ {name}: {len(df):,} rows")
    conn.close()
    print(f"\n🎉 Database saved → {db_path}")
    print(f"   Total: {sum(len(d) for d in tables.values()):,} records across {len(STORES)} stores, {len(RETAILERS_LIST)} retailers")


if __name__ == "__main__":
    save_to_sqlite()
