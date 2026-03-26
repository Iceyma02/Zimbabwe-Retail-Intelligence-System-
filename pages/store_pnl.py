"""Page Name"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os
from dash import html, dcc, callback, Input, Output, State
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

dash.register_page(__name__, path="/pnl", name="Store P&L", order=3)
def layout():
    stores = get_stores()
    store_options = [{"label": "All Stores", "value": "ALL"}] + [
        {"label": r["name"], "value": r["store_id"]} for _, r in stores.iterrows()
    ]
    return html.Div([
        page_header("Store P&L Engine", "Full profit & loss breakdown per store — revenue minus every cost layer", "fa-coins"),
        html.Div([
            html.Div([
                dcc.Dropdown(id="pnl-store", options=store_options, value="ALL", clearable=False,
                             style={"width": "220px", "background": "#1e1e1e", "color": "#fff"}),
                dcc.Dropdown(id="pnl-month", options=[{"label": "Last 3 Months", "value": 3},
                                                       {"label": "Last 6 Months", "value": 6},
                                                       {"label": "Last 12 Months", "value": 12}],
                             value=3, clearable=False,
                             style={"width": "180px", "background": "#1e1e1e", "color": "#fff"}),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "20px"}),

            html.Div(id="pnl-kpis", style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),

            html.Div([
                html.Div([
                    dcc.Graph(id="pnl-waterfall", config={"displayModeBar": False}, style={"height": "340px"})
                ], style={"flex": "1.2", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="pnl-cost-breakdown", config={"displayModeBar": False}, style={"height": "340px"})
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),

            html.Div([
                dcc.Graph(id="pnl-monthly-trend", config={"displayModeBar": False}, style={"height": "260px"})
            ], style={"background": "#161616", "border": "1px solid #222",
                      "borderRadius": "10px", "padding": "16px"}),

        ], style={"padding": "20px 28px"})
    ])


@callback(
    Output("pnl-kpis", "children"),
    Output("pnl-waterfall", "figure"),
    Output("pnl-cost-breakdown", "figure"),
    Output("pnl-monthly-trend", "figure"),
    Input("pnl-store", "value"),
    Input("pnl-month", "value")
)
def update_pnl(store_id, months):
    costs_df = get_store_costs()
    sales_df = get_sales(months * 30)

    if store_id != "ALL":
        costs_df = costs_df[costs_df["store_id"] == store_id]
        sales_df = sales_df[sales_df["store_id"] == store_id]

    # Aggregate
    total_revenue = sales_df["revenue"].sum()
    total_cogs = sales_df["cost"].sum()
    gross_profit = total_revenue - total_cogs

    total_rent = costs_df["rent_usd"].sum()
    total_labour = costs_df["labour_usd"].sum()
    total_utilities = costs_df["utilities_usd"].sum()
    total_security = costs_df["security_usd"].sum()
    total_maintenance = costs_df["maintenance_usd"].sum()
    total_other = costs_df["other_usd"].sum()
    total_opex = total_rent + total_labour + total_utilities + total_security + total_maintenance + total_other
    net_profit = gross_profit - total_opex
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    # KPIs
    kpis = [
        kpi_card("Revenue", f"${total_revenue:,.0f}", None, None, "fa-dollar-sign", "#00c853"),
        kpi_card("Gross Profit", f"${gross_profit:,.0f}", None, None, "fa-chart-line", "#3b82f6"),
        kpi_card("Total OpEx", f"${total_opex:,.0f}", None, None, "fa-money-bill-wave", "#f97316"),
        kpi_card("Net Profit", f"${net_profit:,.0f}", None, None, "fa-coins",
                 "#22c55e" if net_profit > 0 else "#ef4444"),
        kpi_card("Net Margin", f"{net_margin:.1f}%", None, None, "fa-percent",
                 "#22c55e" if net_margin > 8 else "#ef4444"),
    ]

    # Waterfall P&L
    wf_values = [total_revenue, -total_cogs, -total_rent, -total_labour,
                 -total_utilities, -total_security, -total_maintenance, -total_other]
    wf_labels = ["Revenue", "COGS", "Rent", "Labour", "Utilities", "Security", "Maintenance", "Other"]
    wf_colors = ["#22c55e"] + ["#ef4444"] * 7

    fig_wf = go.Figure(go.Waterfall(
        name="P&L", orientation="v",
        measure=["absolute"] + ["relative"] * 7,
        x=wf_labels, y=wf_values,
        connector={"line": {"color": "#333"}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#22c55e"}},
        totals={"marker": {"color": "#3b82f6"}}
    ))
    fig_wf.update_layout(**CHART_LAYOUT, title={"text": "P&L Waterfall", "font": {"color": "#ccc", "size": 13}})

    # Cost breakdown pie
    cost_labels = ["COGS", "Labour", "Rent", "Utilities", "Security", "Maintenance", "Other"]
    cost_vals = [total_cogs, total_labour, total_rent, total_utilities,
                 total_security, total_maintenance, total_other]
    fig_pie = go.Figure(go.Pie(
        labels=cost_labels, values=cost_vals,
        hole=0.4,
        marker={"colors": ["#00c853", "#3b82f6", "#f97316", "#8b5cf6", "#06b6d4", "#eab308", "#888"]}
    ))
    fig_pie.update_layout(**CHART_LAYOUT, title={"text": "Cost Structure", "font": {"color": "#ccc", "size": 13}},
                          showlegend=True)

    # Monthly trend
    sales_monthly = sales_df.copy()
    sales_monthly["month"] = pd.to_datetime(sales_monthly["date"]).dt.to_period("M").astype(str)
    monthly_rev = sales_monthly.groupby("month").agg(revenue=("revenue", "sum"), profit=("profit", "sum")).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=monthly_rev["month"], y=monthly_rev["revenue"],
                                name="Revenue", marker_color="#3b82f6", opacity=0.8))
    fig_trend.add_trace(go.Bar(x=monthly_rev["month"], y=monthly_rev["profit"],
                                name="Gross Profit", marker_color="#22c55e", opacity=0.8))
    fig_trend.update_layout(**CHART_LAYOUT, barmode="group",
                             title={"text": "Monthly Revenue vs Gross Profit", "font": {"color": "#ccc", "size": 13}})

    return [html.Div(k, style={"flex": 1}) for k in kpis], fig_wf, fig_pie, fig_trend
