"""Page Name"""
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
            # Filters
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
            ], style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "20px",
                      "flexWrap": "wrap"}),

            # Summary KPIs
            html.Div(id="inv-kpis", style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),

            # Charts
            html.Div([
                html.Div([
                    dcc.Graph(id="inv-status-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="inv-category-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="inv-expiry-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),

            # Inventory table
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
    Input("inv-store", "value"),
    Input("inv-category", "value"),
    Input("inv-status-filter", "value")
)
def update_inventory(store_id, category, status_filter):
    df = get_inventory_simple()
    if store_id != "ALL":
        df = df[df["store_id"] == store_id]
    if category != "All":
        df = df[df["category"] == category]
    if status_filter != "ALL":
        df = df[df["status"] == status_filter]

    total_skus = len(df)
    critical = len(df[df["status"] == "CRITICAL"])
    low = len(df[df["status"] == "LOW"])
    expiring_3d = len(df[df["days_until_expiry"] <= 3])
    inv_value = (df["current_stock"] * df["unit_cost"]).sum()

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
    fig_expiry.update_layout(**CHART_LAYOUT, title={"text": "Expiry Urgency Breakdown", "font": {"color": "#ccc", "size": 13}})

    # Table
    display_df = df.sort_values("days_until_expiry").head(100)
    headers = ["Product", "Category", "Store", "Stock", "Reorder Point", "Status", "Expiry"]
    header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                             "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                          for h in headers])
    rows = []
    for _, row in display_df.iterrows():
        stock_pct = row["current_stock"] / max(row["reorder_point"], 1) * 100
        stock_color = "#ef4444" if row["status"] == "CRITICAL" else "#f97316" if row["status"] == "LOW" else "#22c55e"
        rows.append(html.Tr([
            html.Td(row["product_name"][:30], style={"color": "#ddd", "padding": "6px 10px", "fontSize": "12px"}),
            html.Td(row["category"], style={"color": "#888", "padding": "6px 10px", "fontSize": "11px"}),
            html.Td(row["store_name"], style={"color": "#888", "padding": "6px 10px", "fontSize": "11px"}),
            html.Td(str(row["current_stock"]), style={"color": stock_color, "padding": "6px 10px", "fontWeight": "600"}),
            html.Td(str(row["reorder_point"]), style={"color": "#666", "padding": "6px 10px"}),
            html.Td(status_badge(row["status"]), style={"padding": "6px 10px"}),
            html.Td(f"{int(row['days_until_expiry'])}d",
                    style={"color": "#ef4444" if row["days_until_expiry"] <= 3 else "#aaa",
                           "padding": "6px 10px", "fontSize": "12px"}),
        ], style={"borderBottom": "1px solid #1a1a1a"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width": "100%", "borderCollapse": "collapse"})

    return [html.Div(k, style={"flex": 1}) for k in kpis], fig_status, fig_cat, fig_expiry, table
