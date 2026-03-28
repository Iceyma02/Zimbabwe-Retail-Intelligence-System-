"""
Central database access layer — all pages import from here
"""
import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "zimretail_iq.db")

print(f"[DEBUG] Database path: {DB_PATH}")
print(f"[DEBUG] Database exists: {os.path.exists(DB_PATH)}")


def get_conn():
    return sqlite3.connect(DB_PATH)


def query(sql, params=None):
    conn = get_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def get_stores(retailer_filter=None):
    sql = "SELECT * FROM stores"
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE retailer_id = '{retailer_filter}'"
    return query(sql)


def get_products():
    return query("SELECT * FROM products")


def get_suppliers():
    return query("SELECT * FROM suppliers")


def get_sales(days=90, retailer_filter=None):
    sql = f"""
        SELECT s.*, p.name as product_name, p.category, p.brand,
               st.name as store_name, st.city, st.retailer_id
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_inventory_simple(retailer_filter=None):
    sql = """
        SELECT i.*, 
               p.name as product_name, 
               p.category, 
               p.brand,
               p.unit_price, 
               p.unit_cost, 
               p.reorder_point, 
               p.reorder_qty, 
               p.shelf_life_days,
               s.name as store_name, 
               s.city,
               s.retailer_id,
               sup.name as supplier_name
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN stores s ON i.store_id = s.store_id
        LEFT JOIN suppliers sup ON p.supplier = sup.name
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE s.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_inventory(retailer_filter=None):
    return get_inventory_simple(retailer_filter)


def get_supplier_credit(retailer_filter=None):
    return query("SELECT * FROM supplier_credit")


def get_staff(retailer_filter=None):
    sql = """
        SELECT sf.*, s.city, s.size_sqm, s.retailer_id
        FROM staff sf 
        JOIN stores s ON sf.store_id = s.store_id
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE s.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_shrinkage(retailer_filter=None):
    sql = """
        SELECT sh.*, s.name as store_name, s.city, s.retailer_id
        FROM shrinkage sh 
        JOIN stores s ON sh.store_id = s.store_id
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE s.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_promotions():
    return query("SELECT * FROM promotions")


def get_competitor_prices():
    return query("SELECT * FROM competitor_prices")


def get_store_costs(retailer_filter=None):
    sql = """
        SELECT sc.*, s.name as store_name, s.city, s.retailer_id
        FROM store_costs sc 
        JOIN stores s ON sc.store_id = s.store_id
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE s.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_logistics(retailer_filter=None):
    sql = "SELECT * FROM logistics"
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE retailer_id = '{retailer_filter}'"
    return query(sql)


def get_economic_indicators():
    return query("SELECT * FROM economic_indicators ORDER BY date DESC")


def get_national_kpis(days=30, retailer_filter=None):
    sql = f"""
        SELECT
            COALESCE(SUM(s.revenue), 0) as total_revenue,
            COALESCE(SUM(s.profit), 0) as total_profit,
            COALESCE(SUM(s.units_sold), 0) as total_units,
            COUNT(DISTINCT s.store_id) as active_stores,
            COALESCE(ROUND(SUM(s.profit)*100.0/NULLIF(SUM(s.revenue),0), 1), 0) as margin_pct
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_store_revenue_summary(days=30, retailer_filter=None):
    sql = f"""
        SELECT s.store_id, s.name as store_name, s.city, s.lat, s.lng, s.retailer_id,
               COALESCE(ROUND(SUM(sa.revenue), 2), 0) as total_revenue,
               COALESCE(ROUND(SUM(sa.profit), 2), 0) as total_profit,
               COALESCE(SUM(sa.units_sold), 0) as total_units,
               COALESCE(ROUND(SUM(sa.profit)*100.0/NULLIF(SUM(sa.revenue),0), 1), 0) as margin_pct
        FROM stores s
        LEFT JOIN sales sa ON s.store_id = sa.store_id AND sa.date >= date('now', '-{days} days')
        GROUP BY s.store_id
        ORDER BY total_revenue DESC
    """
    if retailer_filter and retailer_filter != "ALL":
        sql = sql.replace("FROM stores s", f"FROM stores s WHERE s.retailer_id = '{retailer_filter}'")
    return query(sql)


def get_category_sales(days=30, retailer_filter=None):
    sql = f"""
        SELECT p.category,
               COALESCE(ROUND(SUM(s.revenue), 2), 0) as revenue,
               COALESCE(SUM(s.units_sold), 0) as units
        FROM sales s 
        JOIN products p ON s.product_id = p.product_id
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    sql += " GROUP BY p.category ORDER BY revenue DESC"
    return query(sql)


def get_daily_trend(days=60, retailer_filter=None):
    sql = f"""
        SELECT s.date, COALESCE(ROUND(SUM(s.revenue), 2), 0) as revenue,
               COALESCE(ROUND(SUM(s.profit), 2), 0) as profit
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    sql += " GROUP BY s.date ORDER BY s.date"
    return query(sql)
