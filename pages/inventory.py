"""Inventory Monitor — Page 4 with Retailer Filter"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/inventory", name="Inventory Monitor", order=4)

def layout():
    stores = get_stores()
    store_options = [{"label": "All Stores", "value": "ALL"}] + [
        {"label": r["name"], "value": r["store_id"]} for _, r in stores.iterrows()
    ]
    cats = ["All", "Dairy", "Cooking", "Beverages", "Bakery", "Staples", "Meat", "Snacks", "Personal Care", "Household"]

    return html.Div([
        page_header("Inventory Monitor", "Real-time stock levels, expiry tracking and status alerts", "fa-boxes-stacked"),
        html.Div([
            html.Div([
                dcc.Dropdown(id="inv-store", options=store_options, value="ALL", clearable=False,
                             placeholder="Select store", style={"width": "200px"}),
                dcc.Dropdown(id="inv-category",
                             options=[{"label": c, "value": c} for c in cats],
                             value="All", clearable=False,
                             style={"width": "160px"}),
                dcc.RadioItems(id="inv-status-filter",
                               options=[{"label": f"  {s}", "value": s}
                                        for s in ["ALL", "CRITICAL", "LOW", "ADEQUATE", "GOOD"]],
                               value="ALL", inline=True,
                               inputStyle={"marginRight": "4px", "accentColor": "#00c853"},
                               labelStyle={"marginRight": "16px", "color": "#ccc", "fontSize": "13px"})
            ], style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            html.Div(id="inv-kpis", style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                html.Div([
                    dcc.Graph(id="inv-status-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="inv-category-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="inv-expiry-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                html.Div([
                    html.Div("⚠️ Reorder Priority Alerts", style={
                        "color": "#f97316", "fontSize": "12px", "fontWeight": "600",
                        "marginBottom": "12px", "display": "flex", "alignItems": "center", "gap": "8px"
                    }),
                    html.Div(id="priority-alerts", style={"maxHeight": "200px", "overflowY": "auto"})
                ], style={"background": "#1a1500", "border": "1px solid #f9731630",
                          "borderRadius": "10px", "padding": "16px", "marginBottom": "20px"})
            ], id="priority-alerts-section"),
            html.Div([
                html.Div("Stock Level Detail", style={"color": "#888", "fontSize": "11px",
                                                       "textTransform": "uppercase", "letterSpacing": "1px",
                                                       "marginBottom": "14px"}),
                html.Div(id="inv-table", style={"maxHeight": "400px", "overflowY": "auto"})
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"})
        ], style={"padding": "20px 28px"})
    ])


@callback(
    Output("inv-kpis", "children"),
    Output("inv-status-chart", "figure"),
    Output("inv-category-chart", "figure"),
    Output("inv-expiry-chart", "figure"),
    Output("inv-table", "children"),
    Output("priority-alerts", "children"),
    Output("priority-alerts-section", "style"),
    Input("inv-store", "value"),
    Input("inv-category", "value"),
    Input("inv-status-filter", "value"),
    Input("active-retailer", "data")
)
def update_inventory(store_id, category, status_filter, retailer):
    try:
        df = get_inventory_simple(retailer)
        
        if df.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(**CHART_LAYOUT, title={"text": f"No inventory data for {retailer}"})
            return [], empty_fig, empty_fig, empty_fig, html.Div("No inventory data available"), [], {"display": "none"}
        
        # Apply filters
        if store_id != "ALL":
            df = df[df["store_id"] == store_id]
        if category != "All":
            df = df[df["category"] == category]
        if status_filter != "ALL":
            df = df[df["status"] == status_filter]

        total_skus = len(df)
        critical = len(df[df["status"] == "CRITICAL"])
        low = len(df[df["status"] == "LOW"])
        
        # Calculate days until expiry
        if "expiry_date" in df.columns and "days_until_expiry" not in df.columns:
            df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors='coerce')
            df["days_until_expiry"] = (df["expiry_date"] - pd.Timestamp.now()).dt.days
            df["days_until_expiry"] = df["days_until_expiry"].fillna(999).clip(lower=0)
        
        expiring_3d = len(df[df["days_until_expiry"] <= 3]) if "days_until_expiry" in df.columns else 0
        inv_value = (df["current_stock"] * df["unit_cost"]).sum()
        
        # Get sales data for priority alerts
        sales_df = get_sales(30, retailer)
        high_sellers = {}
        if not sales_df.empty:
            avg_sales = sales_df.groupby("product_id")["units_sold"].mean().reset_index()
            avg_sales.columns = ["product_id", "avg_daily_sales"]
            high_sellers = avg_sales.set_index("product_id")["avg_daily_sales"].to_dict()
        
        df["avg_daily_sales"] = df["product_id"].map(high_sellers).fillna(0)
        df["days_of_stock"] = df.apply(
            lambda r: r["current_stock"] / max(r["avg_daily_sales"], 0.5) if r["avg_daily_sales"] > 0 else 999, 
            axis=1
        )
        
        priority_items = df[
            (df["avg_daily_sales"] > 5) & 
            (df["days_of_stock"] < 7) & 
            (df["status"] != "GOOD")
        ].sort_values("days_of_stock").head(10)
        
        priority_alerts = []
        for _, row in priority_items.iterrows():
            days = row["days_of_stock"]
            sales = row["avg_daily_sales"]
            stock = row["current_stock"]
            urgency_color = "#ef4444" if days < 3 else "#f97316"
            priority_alerts.append(html.Div([
                html.Span("🔥", style={"marginRight": "8px", "fontSize": "14px"}),
                html.Div([
                    html.Div(f"{row['product_name'][:35]} - {row['store_name']}", 
                             style={"color": "#ddd", "fontSize": "13px", "fontWeight": "500"}),
                    html.Div([
                        html.Span(f"{stock} units left", style={"color": urgency_color, "fontWeight": "600"}),
                        html.Span(f" • {sales:.0f} units/day avg", style={"color": "#888", "marginLeft": "8px"}),
                        html.Span(f" • {days:.0f} days remaining", style={"color": urgency_color, "marginLeft": "8px"})
                    ], style={"fontSize": "11px"})
                ], style={"flex": 1})
            ], style={"display": "flex", "alignItems": "center", "padding": "8px 0",
                      "borderBottom": "1px solid #2a2a2a"}))

        kpis = [
            kpi_card("Total SKUs", f"{total_skus:,}", None, None, "fa-cubes", "#3b82f6"),
            kpi_card("Critical Items", str(critical), None, None, "fa-circle-exclamation", "#ef4444"),
            kpi_card("Low Stock", str(low), None, None, "fa-triangle-exclamation", "#f97316"),
            kpi_card("Expiring in 3d", str(expiring_3d), None, None, "fa-calendar-xmark", "#eab308"),
            kpi_card("Inventory Value", f"${inv_value:,.0f}", None, None, "fa-dollar-sign", "#22c55e"),
        ]

        # Status pie
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        color_map = {"CRITICAL": "#ef4444", "LOW": "#f97316", "ADEQUATE": "#eab308", "GOOD": "#22c55e"}
        fig_status = go.Figure(go.Pie(
            labels=status_counts["status"], values=status_counts["count"], hole=0.5,
            marker={"colors": [color_map.get(s, "#888") for s in status_counts["status"]]}
        ))
        fig_status.update_layout(**CHART_LAYOUT, title={"text": "Stock Status Distribution", "font": {"color": "#ccc", "size": 13}})

        # Category heatmap
        cat_status = df.groupby(["category", "status"]).size().reset_index(name="count")
        fig_cat = px.bar(cat_status, x="category", y="count", color="status",
                         color_discrete_map=color_map, barmode="stack")
        fig_cat.update_layout(**CHART_LAYOUT, title={"text": "Stock Status by Category", "font": {"color": "#ccc", "size": 13}})
        fig_cat.update_xaxes(tickangle=-30)

        # Expiry urgency
        if "days_until_expiry" in df.columns:
            expiry_bins = pd.cut(df["days_until_expiry"],
                                 bins=[0, 3, 7, 14, 30, 999],
                                 labels=["<3 days", "3-7 days", "7-14 days", "14-30 days", "30+ days"])
            expiry_counts = expiry_bins.value_counts().sort_index().reset_index()
            expiry_counts.columns = ["range", "count"]
            expiry_colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"]
            fig_expiry = go.Figure(go.Bar(
                x=expiry_counts["range"].astype(str), y=expiry_counts["count"],
                marker_color=expiry_colors
            ))
        else:
            fig_expiry = go.Figure()
            fig_expiry.update_layout(**CHART_LAYOUT, title={"text": "No expiry data", "font": {"color": "#ccc"}})
        fig_expiry.update_layout(**CHART_LAYOUT, title={"text": "Expiry Urgency Breakdown", "font": {"color": "#ccc", "size": 13}})

        # Table
        if "days_until_expiry" in df.columns:
            display_df = df.sort_values("days_until_expiry").head(100)
        else:
            display_df = df.head(100)
            
        headers = ["Product", "Category", "Store", "Stock", "Daily Sales", "Days Left", "Status", "Expiry"]
        header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                                 "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                              for h in headers])
        rows = []
        for _, row in display_df.iterrows():
            stock_color = "#ef4444" if row["status"] == "CRITICAL" else "#f97316" if row["status"] == "LOW" else "#22c55e"
            expiry_display = f"{int(row['days_until_expiry'])}d" if "days_until_expiry" in row and pd.notna(row.get('days_until_expiry', 0)) else "N/A"
            expiry_color = "#ef4444" if "days_until_expiry" in row and row.get('days_until_expiry', 999) <= 3 else "#aaa"
            daily_sales = row.get("avg_daily_sales", 0)
            days_left = row.get("days_of_stock", 999)
            
            rows.append(html.Tr([
                html.Td(row["product_name"][:30], style={"color": "#ddd", "padding": "6px 10px", "fontSize": "12px"}),
                html.Td(row["category"], style={"color": "#888", "padding": "6px 10px", "fontSize": "11px"}),
                html.Td(row["store_name"], style={"color": "#888", "padding": "6px 10px", "fontSize": "11px"}),
                html.Td(str(row["current_stock"]), style={"color": stock_color, "padding": "6px 10px", "fontWeight": "600"}),
                html.Td(f"{daily_sales:.0f}/d" if daily_sales > 0 else "—", 
                        style={"color": "#3b82f6" if daily_sales > 5 else "#888", "padding": "6px 10px"}),
                html.Td(f"{days_left:.0f}d" if days_left < 999 else "—",
                        style={"color": stock_color, "padding": "6px 10px", "fontWeight": "600"}),
                html.Td(status_badge(row["status"]), style={"padding": "6px 10px"}),
                html.Td(expiry_display,
                        style={"color": expiry_color, "padding": "6px 10px", "fontSize": "12px"}),
            ], style={"borderBottom": "1px solid #1a1a1a"}))

        table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                           style={"width": "100%", "borderCollapse": "collapse"})

        show_alerts = len(priority_alerts) > 0
        alerts_style = {"display": "block"} if show_alerts else {"display": "none"}

        return [html.Div(k, style={"flex": 1}) for k in kpis], fig_status, fig_cat, fig_expiry, table, priority_alerts, alerts_style
        
    except Exception as e:
        print(f"Error in inventory callback: {e}")
        import traceback
        traceback.print_exc()
        empty_fig = go.Figure()
        empty_fig.update_layout(**CHART_LAYOUT, title={"text": f"Error: {str(e)[:50]}"})
        return [], empty_fig, empty_fig, empty_fig, html.Div(f"Error loading inventory: {e}"), [], {"display": "none"}
