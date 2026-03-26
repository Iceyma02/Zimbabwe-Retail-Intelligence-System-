"""
Central database access layer — all pages import from here
"""
import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "zimretail_iq.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def query(sql, params=None):
    conn = get_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
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
               p.unit_price, p.unit_cost, p.reorder_point, p.reorder_qty,
               s.name as store_name, s.city
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN stores s ON i.store_id = s.store_id
    """)


def get_inventory_simple():
    """Returns inventory with all product and store info"""
    return query("""
        SELECT i.*, p.name as product_name, p.category, p.brand,
               p.unit_price, p.unit_cost, p.reorder_point, p.reorder_qty, p.shelf_life_days,
               s.name as store_name, s.city, s.retailer_id
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
    result = query(f"""
        SELECT
            COALESCE(SUM(revenue), 0) as total_revenue,
            COALESCE(SUM(profit), 0) as total_profit,
            COALESCE(SUM(units_sold), 0) as total_units,
            COUNT(DISTINCT store_id) as active_stores,
            COALESCE(ROUND(SUM(profit)*100.0/NULLIF(SUM(revenue),0), 1), 0) as margin_pct
        FROM sales
        WHERE date >= date('now', '-{days} days')
    """)
    return result


def get_store_revenue_summary(days=30):
    return query(f"""
        SELECT s.store_id, s.name as store_name, s.city, s.lat, s.lng,
               COALESCE(ROUND(SUM(sa.revenue), 2), 0) as total_revenue,
               COALESCE(ROUND(SUM(sa.profit), 2), 0) as total_profit,
               COALESCE(SUM(sa.units_sold), 0) as total_units,
               COALESCE(ROUND(SUM(sa.profit)*100.0/NULLIF(SUM(sa.revenue),0), 1), 0) as margin_pct
        FROM stores s
        LEFT JOIN sales sa ON s.store_id = sa.store_id AND sa.date >= date('now', '-{days} days')
        GROUP BY s.store_id
        ORDER BY total_revenue DESC
    """)


def get_category_sales(days=30):
    return query(f"""
        SELECT p.category,
               COALESCE(ROUND(SUM(s.revenue), 2), 0) as revenue,
               COALESCE(SUM(s.units_sold), 0) as units
        FROM sales s 
        JOIN products p ON s.product_id = p.product_id
        WHERE s.date >= date('now', '-{days} days')
        GROUP BY p.category ORDER BY revenue DESC
    """)


def get_daily_trend(days=60):
    return query(f"""
        SELECT date, COALESCE(ROUND(SUM(revenue), 2), 0) as revenue,
               COALESCE(ROUND(SUM(profit), 2), 0) as profit
        FROM sales
        WHERE date >= date('now', '-{days} days')
        GROUP BY date ORDER BY date
    """)
