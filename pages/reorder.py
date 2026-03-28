"""Reorder Optimizer — Page 8"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import get_inventory_simple, get_sales
from components.shared import page_header, kpi_card, status_badge, CHART_LAYOUT

dash.register_page(__name__, path="/reorder", name="Reorder Optimizer", order=7)

def flatten_numeric(val):
    """Flatten nested numeric values"""
    if val is None:
        return 0.0
    if isinstance(val, (list, tuple, np.ndarray)):
        if len(val) > 0:
            try:
                return float(val[0])
            except:
                return 0.0
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def flatten_string(val):
    """Flatten nested string values"""
    if val is None:
        return ""
    if isinstance(val, (list, tuple, np.ndarray)):
        if len(val) > 0:
            return str(val[0])
        return ""
    return str(val)

def get_reorder_data():
    """Get products that need reordering with urgency scores"""
    try:
        inv = get_inventory_simple()
        
        if inv.empty:
            print("Warning: No inventory data found")
            return pd.DataFrame()
        
        # Reset index
        inv = inv.reset_index(drop=True)
        
        # Flatten all columns
        if "product_id" in inv.columns:
            inv["product_id"] = inv["product_id"].apply(flatten_string)
        
        if "product_name" in inv.columns:
            inv["product_name"] = inv["product_name"].apply(flatten_string)
        
        if "store_name" in inv.columns:
            inv["store_name"] = inv["store_name"].apply(flatten_string)
        
        # Flatten numeric columns
        numeric_cols = ["current_stock", "reorder_point", "reorder_qty", "unit_cost"]
        for col in numeric_cols:
            if col in inv.columns:
                inv[col] = inv[col].apply(flatten_numeric)
            else:
                inv[col] = 0
        
        # Get 30-day sales data
        sales_30 = get_sales(30)
        
        # Calculate average daily sales per product
        if not sales_30.empty:
            # Flatten product_id in sales
            if "product_id" in sales_30.columns:
                sales_30["product_id"] = sales_30["product_id"].apply(flatten_string)
            
            # Flatten units_sold
            sales_30["units_sold"] = sales_30["units_sold"].apply(flatten_numeric)
            
            avg_daily = sales_30.groupby("product_id")["units_sold"].mean().reset_index()
            avg_daily.columns = ["product_id", "avg_daily_sales"]
            
            # Ensure both are strings for merge
            avg_daily["product_id"] = avg_daily["product_id"].astype(str)
            inv["product_id"] = inv["product_id"].astype(str)
            
            df = inv.merge(avg_daily, on="product_id", how="left")
        else:
            df = inv.copy()
            df["avg_daily_sales"] = 1.0
        
        # Fill missing values
        df["avg_daily_sales"] = df["avg_daily_sales"].fillna(1.0)
        df["avg_daily_sales"] = df["avg_daily_sales"].clip(lower=0.1)
        
        # Calculate days of stock
        df["days_of_stock"] = (df["current_stock"] / df["avg_daily_sales"]).round(1)
        df["days_of_stock"] = df["days_of_stock"].replace([float('inf'), -float('inf')], 999)
        df["days_of_stock"] = df["days_of_stock"].fillna(999)
        
        # Check if reorder is needed - ensure both are 1D arrays
        current_stock = df["current_stock"].values.flatten() if hasattr(df["current_stock"].values, 'flatten') else df["current_stock"].values
        reorder_point = df["reorder_point"].values.flatten() if hasattr(df["reorder_point"].values, 'flatten') else df["reorder_point"].values
        
        # Ensure they have the same shape
        if len(current_stock.shape) > 1:
            current_stock = current_stock.flatten()
        if len(reorder_point.shape) > 1:
            reorder_point = reorder_point.flatten()
        
        df["reorder_needed"] = current_stock <= reorder_point
        
        needs_reorder = df[df["reorder_needed"]].copy()
        
        if needs_reorder.empty:
            return needs_reorder
        
        # Calculate urgency score
        needs_reorder["urgency_score"] = (
            (1 / (needs_reorder["days_of_stock"] + 0.5)) * 0.6 +
            (needs_reorder["reorder_point"] / (needs_reorder["current_stock"] + 1)) * 0.4
        )
        
        needs_reorder["urgency_score"] = needs_reorder["urgency_score"].replace([float('inf'), -float('inf')], 1.0)
        needs_reorder["urgency_score"] = needs_reorder["urgency_score"].fillna(1.0)
        
        return needs_reorder.sort_values("urgency_score", ascending=False)
        
    except Exception as e:
        print(f"Error in get_reorder_data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def layout():
    """Layout for reorder optimizer page"""
    try:
        needs_reorder = get_reorder_data()
        
        if needs_reorder.empty:
            return html.Div([
                page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div("✅ All Stock Levels Healthy", style={
                                "fontSize": "24px", "fontWeight": "700", "color": "#22c55e", "marginBottom": "16px"
                            }),
                            html.Div("No items currently need reordering. All stock levels are above reorder points.",
                                    style={"color": "#888", "fontSize": "14px"}),
                        ], style={"textAlign": "center", "padding": "60px"})
                    ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "40px"})
                ], style={"padding": "20px 28px"})
            ])
        
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
            x=top20["urgency_score"].round(2), 
            y=top20["product_name"].str[:35],
            orientation="h",
            marker_color=["#ef4444" if d < 3 else "#f97316" if d < 7 else "#eab308"
                          for d in top20["days_of_stock"]],
            text=top20["days_of_stock"].apply(lambda x: f"{x:.0f}d left"),
            textposition="outside",
            textfont={"size": 10}
        ))
        chart_layout = CHART_LAYOUT.copy()
        chart_layout.update({
            "title": {"text": "Top 20 Items by Reorder Urgency Score", "font": {"color": "#ccc", "size": 13}},
            "yaxis": {"categoryorder": "total ascending", "automargin": True},
            "height": 500,
            "margin": {"l": 150}
        })
        fig.update_layout(**chart_layout)

        # Table
        headers = ["Product", "Store", "Current Stock", "Days Left", "Reorder Qty", "Order Value", "Urgency"]
        header_row = html.Tr([html.Th(h, style={
            "color": "#666", "fontSize": "11px", "padding": "8px 10px",
            "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"
        }) for h in headers])
        
        rows = []
        max_score = needs_reorder["urgency_score"].max() if len(needs_reorder) > 0 else 1
        
        for _, row in needs_reorder.head(50).iterrows():
            days = row["days_of_stock"]
            urgency_color = "#ef4444" if days < 3 else "#f97316" if days < 7 else "#eab308"
            order_val = row["reorder_qty"] * row["unit_cost"]
            urgency_pct = min(row["urgency_score"] / max_score * 100, 100)
            
            rows.append(html.Tr([
                html.Td(row["product_name"][:28], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
                html.Td(str(row["store_name"])[:20], style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
                html.Td(str(row["current_stock"]), style={"color": urgency_color", "padding": "7px 10px", "fontWeight": "600"}),
                html.Td(f"{days:.0f}d", style={"color": urgency_color", "padding": "7px 10px", "fontWeight": "600"}),
                html.Td(str(int(row["reorder_qty"])), style={"color": "#3b82f6", "padding": "7px 10px"}),
                html.Td(f"${order_val:,.0f}", style={"color": "#22c55e", "padding": "7px 10px"}),
                html.Td(html.Div(style={
                    "width": f"{urgency_pct:.0f}%",
                    "height": "6px", "background": urgency_color, "borderRadius": "3px"
                }), style={"padding": "7px 10px", "width": "80px"}),
            ], style={"borderBottom": "1px solid #1a1a1a"}))
        
        table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                          style={"width": "100%", "borderCollapse": "collapse"})

        return html.Div([
            page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
            html.Div([
                html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                         style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
                html.Div([
                    dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "500px"})
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
        
    except Exception as e:
        print(f"Error in reorder layout: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
            html.Div([
                html.Div([
                    html.Div("⚠️ Error Loading Data", style={
                        "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
                    }),
                    html.Div(str(e), style={"color": "#888", "fontSize": "14px"}),
                    html.Div("Please check that the database contains inventory data.",
                            style={"color": "#666", "fontSize": "12px", "marginTop": "12px"})
                ], style={"textAlign": "center", "padding": "60px"})
            ], style={"padding": "20px 28px"})
        ])
