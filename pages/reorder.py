"""Reorder Optimizer — Page 8"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from data.db
from data.db import (
    get_stores, get_products, get_sales, get_inventory_simple,
    get_supplier_credit, get_staff, get_shrinkage, get_promotions,
    get_competitor_prices, get_store_costs, get_logistics,
    get_economic_indicators, get_national_kpis, get_store_revenue_summary,
    get_category_sales, get_daily_trend
)

# Import from components
from components.shared import page_header, kpi_card, status_badge, CHART_LAYOUT

dash.register_page(__name__, path="/page-path", name="Page Name", order=0)

def get_reorder_data():
    inv = get_inventory_simple()
    sales_30 = get_sales(30)
    avg_daily = sales_30.groupby("product_id")["units_sold"].mean().reset_index()
    avg_daily.columns = ["product_id", "avg_daily_sales"]
    df = inv.merge(avg_daily, on="product_id", how="left")
    df["avg_daily_sales"] = df["avg_daily_sales"].fillna(1)
    df["days_of_stock"] = (df["current_stock"] / df["avg_daily_sales"]).round(1)
    df["reorder_needed"] = df["current_stock"] <= df["reorder_point"]
    needs_reorder = df[df["reorder_needed"]].copy()
    needs_reorder["urgency_score"] = (
        (1 / (needs_reorder["days_of_stock"] + 0.1)) * 0.6 +
        (needs_reorder["reorder_point"] / (needs_reorder["current_stock"] + 1)) * 0.4
    )
    return needs_reorder.sort_values("urgency_score", ascending=False)

def layout():
    needs_reorder = get_reorder_data()

    total_need = len(needs_reorder)
    critical_need = len(needs_reorder[needs_reorder["days_of_stock"] < 3])
    total_order_value = (needs_reorder["reorder_qty"] * needs_reorder["unit_cost"]).sum()

    kpis = [
        kpi_card("Items to Reorder", str(total_need), None, None, "fa-rotate", "#f97316"),
        kpi_card("Critical (<3 days)", str(critical_need), None, None, "fa-fire", "#ef4444"),
        kpi_card("Est. Order Value", f"${total_order_value:,.0f}", None, None, "fa-dollar-sign", "#3b82f6"),
    ]

    # Urgency chart
    top20 = needs_reorder.head(20)
    fig = go.Figure(go.Bar(
        x=top20["urgency_score"].round(2), y=top20["product_name"].str[:25],
        orientation="h",
        marker_color=["#ef4444" if d < 3 else "#f97316" if d < 7 else "#eab308"
                      for d in top20["days_of_stock"]]
    ))
    fig.update_layout(**CHART_LAYOUT,
                      title={"text": "Top 20 Items by Reorder Urgency Score", "font": {"color": "#ccc", "size": 13}},
                      yaxis={"categoryorder": "total ascending"})

    # Table
    headers = ["Product", "Store", "Current Stock", "Days Left", "Reorder Qty", "Order Value", "Urgency"]
    header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                             "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                          for h in headers])
    rows = []
    max_score = needs_reorder["urgency_score"].max() if len(needs_reorder) > 0 else 1
    for _, row in needs_reorder.head(50).iterrows():
        days = row["days_of_stock"]
        urgency_color = "#ef4444" if days < 3 else "#f97316" if days < 7 else "#eab308"
        order_val = row["reorder_qty"] * row["unit_cost"]
        rows.append(html.Tr([
            html.Td(row["product_name"][:28], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
            html.Td(row["store_name"], style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
            html.Td(str(row["current_stock"]), style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
            html.Td(f"{days:.1f}d", style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
            html.Td(str(int(row["reorder_qty"])), style={"color": "#3b82f6", "padding": "7px 10px"}),
            html.Td(f"${order_val:,.0f}", style={"color": "#22c55e", "padding": "7px 10px"}),
            html.Td(html.Div(style={
                "width": f"{min(row['urgency_score']/max_score*100, 100):.0f}%",
                "height": "6px", "background": urgency_color, "borderRadius": "3px"
            }), style={"padding": "7px 10px", "width": "80px"}),
        ], style={"borderBottom": "1px solid #1a1a1a"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width": "100%", "borderCollapse": "collapse"})

    return html.Div([
        page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
        html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "280px"})
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px",
                      "padding": "16px", "marginBottom": "14px"}),
            html.Div([
                html.Div("Reorder Queue — Prioritised by Urgency", style={
                    "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                    "letterSpacing": "1px", "marginBottom": "14px"
                }),
                table
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
        ], style={"padding": "20px 28px"})
    ])
