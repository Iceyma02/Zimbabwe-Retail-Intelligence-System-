"""Reorder Optimizer — Page 8 - Enhanced with Supplier Credit Risk & Forecasting"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import get_inventory_simple, get_sales, get_supplier_credit, get_daily_trend
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

def simple_forecast(sales_series, horizon=30):
    """Simple trend forecast for demand prediction"""
    if len(sales_series) < 7:
        return np.array([sales_series.mean()] * horizon)
    
    x = np.arange(len(sales_series))
    y = sales_series.values
    
    # Linear trend
    coeffs = np.polyfit(x, y, 1)
    trend_slope = coeffs[0]
    trend_intercept = coeffs[1]
    
    # Weekly seasonality
    if len(sales_series) >= 14:
        dow_means = sales_series.groupby(sales_series.index.dayofweek).mean()
        global_mean = y.mean()
        dow_factors = (dow_means / global_mean).fillna(1.0).to_dict()
    else:
        dow_factors = {i: 1.0 for i in range(7)}
    
    # Generate forecast
    forecast = []
    for i in range(horizon):
        trend_val = trend_slope * (len(y) + i) + trend_intercept
        dow_factor = dow_factors.get((pd.Timestamp.now() + pd.Timedelta(days=i)).dayofweek, 1.0)
        pred = max(0, trend_val * dow_factor)
        forecast.append(pred)
    
    return np.array(forecast)

def get_reorder_data():
    """Get products that need reordering with urgency scores including supplier risk"""
    try:
        inv = get_inventory_simple()
        
        if inv.empty:
            print("Warning: No inventory data found")
            return pd.DataFrame()
        
        # Get supplier credit data for risk scoring
        supplier_credit = get_supplier_credit()
        
        # Create supplier risk dictionary
        supplier_risk = {}
        if not supplier_credit.empty:
            for _, row in supplier_credit.iterrows():
                supplier = flatten_string(row.get("supplier_name", ""))
                status = flatten_string(row.get("supplier_status", "ACTIVE"))
                # Risk score: 1 = high risk, 0 = low risk
                risk_score = 1.0 if status == "STOPPED" else 0.6 if status == "LIMITED_CREDIT" else 0.0
                if supplier not in supplier_risk or risk_score > supplier_risk[supplier]:
                    supplier_risk[supplier] = risk_score
        
        # Reset index
        inv = inv.reset_index(drop=True)
        
        # Flatten all columns
        if "product_id" in inv.columns:
            inv["product_id"] = inv["product_id"].apply(flatten_string)
        
        if "product_name" in inv.columns:
            inv["product_name"] = inv["product_name"].apply(flatten_string)
        
        if "store_name" in inv.columns:
            if isinstance(inv["store_name"], pd.DataFrame):
                inv["store_name"] = inv["store_name"].iloc[:, 0].apply(flatten_string)
            else:
                inv["store_name"] = inv["store_name"].apply(flatten_string)
        
        if "supplier_name" in inv.columns:
            if isinstance(inv["supplier_name"], pd.DataFrame):
                inv["supplier_name"] = inv["supplier_name"].iloc[:, 0].apply(flatten_string)
            else:
                inv["supplier_name"] = inv["supplier_name"].apply(flatten_string)
        else:
            inv["supplier_name"] = "Unknown"
        
        # Flatten numeric columns
        numeric_cols = ["current_stock", "reorder_point", "reorder_qty", "unit_cost"]
        for col in numeric_cols:
            if col in inv.columns:
                if isinstance(inv[col], pd.DataFrame):
                    inv[col] = inv[col].iloc[:, 0].apply(flatten_numeric)
                else:
                    inv[col] = inv[col].apply(flatten_numeric)
            else:
                inv[col] = 0
        
        # Get 90-day sales data for better forecasting
        sales_90 = get_sales(90)
        
        # Calculate forecasted demand per product
        product_forecast = {}
        if not sales_90.empty:
            # Flatten product_id in sales
            if "product_id" in sales_90.columns:
                if isinstance(sales_90["product_id"], pd.DataFrame):
                    sales_90["product_id"] = sales_90["product_id"].iloc[:, 0].apply(flatten_string)
                else:
                    sales_90["product_id"] = sales_90["product_id"].apply(flatten_string)
            
            sales_90["units_sold"] = sales_90["units_sold"].apply(flatten_numeric)
            sales_90["date"] = pd.to_datetime(sales_90["date"])
            
            # Forecast for each product
            for product_id in inv["product_id"].unique():
                product_sales = sales_90[sales_90["product_id"] == product_id].copy()
                if not product_sales.empty:
                    product_sales = product_sales.set_index("date")["units_sold"].resample("D").sum().fillna(0)
                    forecast_30d = simple_forecast(product_sales, 30)
                    product_forecast[product_id] = forecast_30d.sum()
                else:
                    product_forecast[product_id] = 0
        
        # Calculate average daily sales using forecast instead of historical
        df = inv.copy()
        df["forecast_30d"] = df["product_id"].map(product_forecast).fillna(0)
        df["forecast_daily"] = df["forecast_30d"] / 30
        df["forecast_daily"] = df["forecast_daily"].clip(lower=0.5)
        
        # Use forecast for days of stock calculation
        df["days_of_stock"] = (df["current_stock"] / df["forecast_daily"]).round(1)
        df["days_of_stock"] = df["days_of_stock"].replace([float('inf'), -float('inf')], 999)
        df["days_of_stock"] = df["days_of_stock"].fillna(999)
        
        # Add supplier risk score
        df["supplier_risk"] = df["supplier_name"].map(supplier_risk).fillna(0)
        
        # Check if reorder is needed
        df["reorder_needed"] = df["current_stock"] <= df["reorder_point"]
        
        # Filter out items from stopped suppliers
        df["reorder_needed"] = df["reorder_needed"] & (df["supplier_risk"] < 1.0)
        
        needs_reorder = df[df["reorder_needed"]].copy()
        
        if needs_reorder.empty:
            return needs_reorder
        
        # Calculate urgency score (higher = more urgent)
        needs_reorder["stock_urgency"] = 1 / (needs_reorder["days_of_stock"] + 0.5)
        needs_reorder["reorder_urgency"] = needs_reorder["reorder_point"] / (needs_reorder["current_stock"] + 1)
        
        # Combine with supplier risk (higher risk = more urgent to pay, but we avoid ordering from stopped)
        needs_reorder["supplier_factor"] = 1 + needs_reorder["supplier_risk"] * 0.5
        
        needs_reorder["urgency_score"] = (
            needs_reorder["stock_urgency"] * 0.5 +
            needs_reorder["reorder_urgency"] * 0.3 +
            (1 - needs_reorder["supplier_risk"]) * 0.2
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
        
        # Get supplier credit data for warning display
        supplier_credit = get_supplier_credit()
        stopped_suppliers = []
        if not supplier_credit.empty:
            for _, row in supplier_credit.iterrows():
                if flatten_string(row.get("supplier_status", "")) == "STOPPED":
                    stopped_suppliers.append(flatten_string(row.get("supplier_name", "")))
        
        if needs_reorder.empty:
            warning_message = ""
            if stopped_suppliers:
                warning_message = html.Div([
                    html.Div("⚠️ Warning: The following suppliers have stopped trading", 
                             style={"color": "#ef4444", "fontWeight": "600", "marginBottom": "8px"}),
                    html.Div(", ".join(stopped_suppliers[:5]), 
                             style={"color": "#888", "fontSize": "12px"}),
                    html.Div("No items from these suppliers are being recommended for reorder.",
                             style={"color": "#666", "fontSize": "12px", "marginTop": "8px"})
                ], style={"background": "#2d0a0a", "border": "1px solid #ef444430", 
                          "borderRadius": "8px", "padding": "12px", "marginBottom": "16px"})
            
            return html.Div([
                page_header("Reorder Optimizer", "Smart reorder suggestions based on stock levels, demand and supplier lead times", "fa-rotate"),
                warning_message if warning_message else None,
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
        blocked_items = len(needs_reorder[needs_reorder["supplier_risk"] >= 1.0]) if "supplier_risk" in needs_reorder.columns else 0

        kpis = [
            kpi_card("Items to Reorder", str(total_need), None, None, "fa-rotate", "#f97316"),
            kpi_card("Critical (<3 days)", str(critical_need), None, None, "fa-fire", "#ef4444"),
            kpi_card("Est. Order Value", f"${total_order_value:,.0f}", None, None, "fa-dollar-sign", "#3b82f6"),
            kpi_card("Blocked by Supplier", str(blocked_items), None, None, "fa-ban", "#ef4444"),
        ]

        # Urgency chart with supplier risk indicators
        top20 = needs_reorder.head(20)
        fig = go.Figure(go.Bar(
            x=top20["urgency_score"].round(2), 
            y=top20["product_name"].str[:35],
            orientation="h",
            marker_color=["#ef4444" if d < 3 else "#f97316" if d < 7 else "#eab308"
                          for d in top20["days_of_stock"]],
            text=[f"{d:.0f}d left" + (f" | Risk: {s:.0%}" if s > 0 else "") 
                  for d, s in zip(top20["days_of_stock"], top20["supplier_risk"])],
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

        # Table with supplier risk indicator
        headers = ["Product", "Store", "Supplier", "Current Stock", "Days Left", "Reorder Qty", "Supplier Risk", "Order Value", "Urgency"]
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
            
            # Supplier risk indicator
            risk = row.get("supplier_risk", 0)
            risk_color = "#ef4444" if risk > 0.8 else "#f97316" if risk > 0.4 else "#22c55e"
            risk_text = "STOPPED" if risk >= 1.0 else "Limited" if risk > 0.4 else "Active"
            
            rows.append(html.Tr([
                html.Td(row["product_name"][:28], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
                html.Td(str(row["store_name"])[:20], style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
                html.Td(str(row.get("supplier_name", "Unknown"))[:15], style={"color": "#aaa", "padding": "7px 10px", "fontSize": "11px"}),
                html.Td(str(row["current_stock"]), style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
                html.Td(f"{days:.0f}d", style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
                html.Td(str(int(row["reorder_qty"])), style={"color": "#3b82f6", "padding": "7px 10px"}),
                html.Td(html.Span(risk_text, style={
                    "background": f"{risk_color}20", "color": risk_color,
                    "padding": "2px 8px", "borderRadius": "12px", "fontSize": "10px"
                }), style={"padding": "7px 10px"}),
                html.Td(f"${order_val:,.0f}", style={"color": "#22c55e", "padding": "7px 10px"}),
                html.Td(html.Div(style={
                    "width": f"{urgency_pct:.0f}%",
                    "height": "6px", "background": urgency_color, "borderRadius": "3px"
                }), style={"padding": "7px 10px", "width": "80px"}),
            ], style={"borderBottom": "1px solid #1a1a1a",
                      "background": "#1a0a0a" if risk >= 0.8 else "transparent"}))
        
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
                    html.Div("Reorder Queue — Prioritised by Urgency (Including Supplier Risk)", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    table
                ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px", "overflowX": "auto"}),
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
