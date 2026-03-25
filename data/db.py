import sqlite3
import pandas as pd
import os

# Works both locally and on Railway regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "zimretail_iq.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def query(sql, params=None):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def get_stores():
    return query("SELECT * FROM stores")


def get_products():
    return query("SELECT * FROM products")


def get_suppliers():
    return query("SELECT * FROM suppliers")


def get_sales(days=90):
    return query(f"""
        SELECT s.*, p.name as product_name, p.category, p.brand,
               st.name as store_name, st.city
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """)


def get_inventory():
    return query("""
        SELECT i.*, p.name as product_name, p.category, p.brand,
               p.unit_price, p.unit_cost, s.name as store_name, s.city,
               sup.name as supplier_name, sup.supplier_id
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN stores s ON i.store_id = s.store_id
        LEFT JOIN (
            SELECT sp.supplier_id, sp.name,
                   json_each.value as product_id_raw
            FROM suppliers sp
        ) sup ON 1=0
    """)


def get_inventory_simple():
    return query("""
        SELECT i.*, p.name as product_name, p.category, p.brand,
               p.unit_price, p.unit_cost, p.shelf_life_days,
               s.name as store_name, s.city
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN stores s ON i.store_id = s.store_id
    """)


def get_supplier_credit():
    return query("SELECT * FROM supplier_credit")


def get_staff():
    return query("""
        SELECT sf.*, s.city, s.size_sqm
        FROM staff sf JOIN stores s ON sf.store_id = s.store_id
    """)


def get_shrinkage():
    return query("""
        SELECT sh.*, s.name as store_name, s.city
        FROM shrinkage sh JOIN stores s ON sh.store_id = s.store_id
    """)


def get_promotions():
    return query("SELECT * FROM promotions")


def get_competitor_prices():
    return query("SELECT * FROM competitor_prices")


def get_store_costs():
    return query("""
        SELECT sc.*, s.name as store_name, s.city
        FROM store_costs sc JOIN stores s ON sc.store_id = s.store_id
    """)


def get_logistics():
    return query("SELECT * FROM logistics")


def get_economic_indicators():
    return query("SELECT * FROM economic_indicators ORDER BY date DESC")


def get_national_kpis(days=30):
    return query(f"""
        SELECT
            SUM(revenue) as total_revenue,
            SUM(profit) as total_profit,
            SUM(units_sold) as total_units,
            COUNT(DISTINCT store_id) as active_stores,
            ROUND(SUM(profit)*100.0/NULLIF(SUM(revenue),0), 1) as margin_pct
        FROM sales
        WHERE date >= date('now', '-{days} days')
    """)


def get_store_revenue_summary(days=30):
    return query(f"""
        SELECT s.store_id, s.name as store_name, s.city, s.lat, s.lng,
               ROUND(SUM(sa.revenue), 2) as total_revenue,
               ROUND(SUM(sa.profit), 2) as total_profit,
               SUM(sa.units_sold) as total_units,
               ROUND(SUM(sa.profit)*100.0/NULLIF(SUM(sa.revenue),0), 1) as margin_pct
        FROM stores s
        JOIN sales sa ON s.store_id = sa.store_id
        WHERE sa.date >= date('now', '-{days} days')
        GROUP BY s.store_id
        ORDER BY total_revenue DESC
    """)


def get_category_sales(days=30):
    return query(f"""
        SELECT p.category,
               ROUND(SUM(s.revenue), 2) as revenue,
               SUM(s.units_sold) as units
        FROM sales s JOIN products p ON s.product_id = p.product_id
        WHERE s.date >= date('now', '-{days} days')
        GROUP BY p.category ORDER BY revenue DESC
    """)


def get_daily_trend(days=60):
    return query(f"""
        SELECT date, ROUND(SUM(revenue), 2) as revenue,
               ROUND(SUM(profit), 2) as profit
        FROM sales
        WHERE date >= date('now', '-{days} days')
        GROUP BY date ORDER BY date
    """)
