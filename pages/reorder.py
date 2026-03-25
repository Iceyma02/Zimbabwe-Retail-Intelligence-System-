"""Reorder Optimizer — Page 8"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/reorder", name="Reorder Optimizer", order=7)

def get_reorder_data():
    """Get products that need reordering with urgency scores"""
    inv = get_inventory_simple()
    
    if inv.empty:
        return pd.DataFrame()
    
    # Get 30-day sales
    sales_30 = get_sales(30)
    
    if sales_30.empty:
        # If no sales data, use inventory only
        inv["avg_daily_sales"] = 1.0
        inv["days_of_stock"] = inv["current_stock"] / inv["avg_daily_sales"]
    else:
        # Calculate average daily sales per product
        avg_daily = sales_30.groupby("product_id")["units_sold"].mean().reset_index()
        avg_daily.columns = ["product_id", "avg_daily_sales"]
        inv = inv.merge(avg_daily, on="product_id", how="left")
        inv["avg_daily_sales"] = inv["avg_daily_sales"].fillna(0.5)  # Default for no sales
        inv["avg_daily_sales"] = inv["avg_daily_sales"].clip(lower=0.1)  # Minimum to avoid division by zero
        inv["days_of_stock"] = (inv["current_stock"] / inv["avg_daily_sales"]).round(1)
    
    # Replace infinite values
    inv["days_of_stock"] = inv["days_of_stock"].replace([float('inf'), -float('inf')], 999)
    
    # Identify items that need reorder
    inv["reorder_needed"] = inv["current_stock"] <= inv["reorder_point"]
    needs_reorder = inv[inv["reorder_needed"]].copy()
    
    if len(needs_reorder) == 0:
        return needs_reorder
    
    # Calculate urgency score
    # Higher score = more urgent
    max_days = needs_reorder["days_of_stock"].max() + 1
    needs_reorder["stock_urgency"] = 1 / (needs_reorder["days_of_stock"] + 0.5)
    
    # Reorder point proximity (how close to zero)
    needs_reorder["reorder_proximity"] = needs_reorder["reorder_point"] / (needs_reorder["current_stock"] + 1)
    
    # Combine scores
    needs_reorder["urgency_score"] = (
        needs_reorder["stock_urgency"] * 0.6 + 
        needs_reorder["reorder_proximity"] * 0.4
    )
    
    return needs_reorder.sort_values("urgency_score", ascending=False)

def layout():
    needs_reorder = get_reorder_data()
    
    total_need = len(needs_reorder)
    critical_need = len(needs_reorder[needs_reorder["days_of_stock"] < 3]) if not needs_reorder.empty else 0
    total_order_value = (needs_reorder["reorder_qty"] * needs_reorder["unit_cost"]).sum() if not needs_reorder.empty else 0

    kpis = [
        kpi_card("Items to Reorder", str(total_need), None, None, "fa-rotate", "#f97316"),
        kpi_card("Critical (<3 days)", str(critical_need), None, None, "fa-fire", "#ef4444"),
        kpi_card("Est. Order Value", f"${total_order_value:,.0f}", None, None, "fa-dollar-sign", "#3b82f6"),
    ]

    return html.Div([
        page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
        html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div(id="reorder-chart", style={"marginBottom": "14px"}),
            html.Div([
                html.Div("Reorder Queue — Prioritised by Urgency", style={
                    "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                    "letterSpacing": "1px", "marginBottom": "14px"
                }),
                html.Div(id="reorder-table")
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
        ], style={"padding": "20px 28px"})
    ])

@callback(
    Output("reorder-chart", "children"),
    Output("reorder-table", "children"),
    Input("reorder", "value")  # Dummy input to trigger callback
)
def update_reorder(_):
    needs_reorder = get_reorder_data()
    
    if needs_reorder.empty:
        empty_msg = html.Div("✅ All stock levels are healthy. No items need reordering at this time.",
                              style={"color": "#22c55e", "textAlign": "center", "padding": "40px"})
        return empty_msg, empty_msg
    
    # Urgency chart
    top20 = needs_reorder.head(20)
    fig = go.Figure(go.Bar(
        x=top20["urgency_score"].round(2), 
        y=top20["product_name"].str[:35],
        orientation="h",
        marker_color=["#ef4444" if d < 3 else "#f97316" if d < 7 else "#eab308"
                      for d in top20["days_of_stock"]],
        text=top20["days_of_stock"].apply(lambda x: f"{x:.0f}d left"),
        textposition="outside",
        textfont={"size": 10}
    ))
    fig.update_layout(**CHART_LAYOUT,
                      title={"text": "Top 20 Items by Reorder Urgency Score", "font": {"color": "#ccc", "size": 13}},
                      yaxis={"categoryorder": "total ascending", "automargin": True},
                      height=500)
    
    chart_div = html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "500px"})
    ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"})
    
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
        urgency_pct = min(row["urgency_score"] / max_score * 100, 100)
        
        rows.append(html.Tr([
            html.Td(row["product_name"][:28], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
            html.Td(row["store_name"], style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
            html.Td(str(row["current_stock"]), style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
            html.Td(f"{days:.0f}d", style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
            html.Td(str(int(row["reorder_qty"])), style={"color": "#3b82f6", "padding": "7px 10px"}),
            html.Td(f"${order_val:,.0f}", style={"color": "#22c55e", "padding": "7px 10px"}),
            html.Td(html.Div(style={
                "width": f"{urgency_pct:.0f}%",
                "height": "6px", "background": urgency_color, "borderRadius": "3px"
            }), style={"padding": "7px 10px", "width": "80px"}),
        ], style={"borderBottom": "1px solid #1a1a1a"}))
    
    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width": "100%", "borderCollapse": "collapse"})
    
    return chart_div, table
