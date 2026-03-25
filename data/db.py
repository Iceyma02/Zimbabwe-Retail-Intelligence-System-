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


def apply_retailer_filter(query, retailer_filter, alias="stores"):
    """Helper to add retailer filter to SQL queries"""
    if retailer_filter and retailer_filter != "ALL":
        return query.replace("WHERE", f"WHERE {alias}.retailer_id = '{retailer_filter}' AND ")
    return query


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
        SELECT i.*, p.name as product_name, p.category, p.brand,
               p.unit_price, p.unit_cost, p.shelf_life_days,
               s.name as store_name, s.city, s.retailer_id
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN stores s ON i.store_id = s.store_id
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" WHERE s.retailer_id = '{retailer_filter}'"
    return query(sql)


def get_supplier_credit(retailer_filter=None):
    sql = "SELECT * FROM supplier_credit"
    # Supplier credit is supplier-level, not retailer-specific
    return query(sql)


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
            SUM(revenue) as total_revenue,
            SUM(profit) as total_profit,
            SUM(units_sold) as total_units,
            COUNT(DISTINCT store_id) as active_stores,
            ROUND(SUM(profit)*100.0/NULLIF(SUM(revenue),0), 1) as margin_pct
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    result = query(sql)
    return result.iloc[0] if not result.empty else None


def get_store_revenue_summary(days=30, retailer_filter=None):
    sql = f"""
        SELECT s.store_id, s.name as store_name, s.city, s.lat, s.lng, s.retailer_id,
               ROUND(SUM(sa.revenue), 2) as total_revenue,
               ROUND(SUM(sa.profit), 2) as total_profit,
               SUM(sa.units_sold) as total_units,
               ROUND(SUM(sa.profit)*100.0/NULLIF(SUM(sa.revenue),0), 1) as margin_pct
        FROM stores s
        JOIN sales sa ON s.store_id = sa.store_id
        WHERE sa.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND s.retailer_id = '{retailer_filter}'"
    sql += " GROUP BY s.store_id ORDER BY total_revenue DESC"
    return query(sql)


def get_category_sales(days=30, retailer_filter=None):
    sql = f"""
        SELECT p.category,
               ROUND(SUM(s.revenue), 2) as revenue,
               SUM(s.units_sold) as units
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
        SELECT date, ROUND(SUM(revenue), 2) as revenue,
               ROUND(SUM(profit), 2) as profit
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        WHERE s.date >= date('now', '-{days} days')
    """
    if retailer_filter and retailer_filter != "ALL":
        sql += f" AND st.retailer_id = '{retailer_filter}'"
    sql += " GROUP BY date ORDER BY date"
    return query(sql)
