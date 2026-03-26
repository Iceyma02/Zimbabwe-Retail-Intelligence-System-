"""Shrinkage & Loss — Page 15"""
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

dash.register_page(__name__, path="/shrinkage", name="Shrinkage & Loss", order=14)

def layout():
    df = get_shrinkage()
    total_loss = df["value_usd"].sum()
    avg_monthly = df.groupby("month")["value_usd"].sum().mean()
    worst_store = df.groupby("store_name")["value_usd"].sum().idxmax()
    theft = df[df["cause"] == "Theft"]["value_usd"].sum()

    kpis = [
        kpi_card("Total Losses (6mo)", f"${total_loss:,.0f}", None, None, "fa-circle-minus", "#ef4444"),
        kpi_card("Avg Monthly Loss", f"${avg_monthly:,.0f}", None, None, "fa-calendar", "#f97316"),
        kpi_card("Theft Losses", f"${theft:,.0f}", None, None, "fa-user-secret", "#8b5cf6"),
        kpi_card("Highest Loss Store", worst_store[:15], None, None, "fa-store", "#eab308"),
    ]

    cause_totals = df.groupby("cause")["value_usd"].sum().sort_values(ascending=False).reset_index()
    fig_cause = go.Figure(go.Bar(
        x=cause_totals["cause"], y=cause_totals["value_usd"],
        marker_color=["#ef4444", "#f97316", "#eab308", "#8b5cf6", "#3b82f6"][:len(cause_totals)]
    ))
    fig_cause.update_layout(**CHART_LAYOUT,
                             title={"text": "Loss by Cause", "font": {"color": "#ccc", "size": 13}})

    store_totals = df.groupby("store_name")["value_usd"].sum().sort_values(ascending=False).reset_index()
    fig_store = go.Figure(go.Bar(
        x=store_totals["value_usd"], y=store_totals["store_name"], orientation="h",
        marker_color=["#ef4444" if i == 0 else "#f97316" if i < 3 else "#3b82f6"
                      for i in range(len(store_totals))]
    ))
    fig_store.update_layout(**CHART_LAYOUT,
                             title={"text": "Loss by Store", "font": {"color": "#ccc", "size": 13}},
                             yaxis={"categoryorder": "total ascending"})

    monthly = df.groupby(["month", "cause"])["value_usd"].sum().reset_index()
    fig_trend = px.bar(monthly, x="month", y="value_usd", color="cause", barmode="stack")
    fig_trend.update_layout(**CHART_LAYOUT,
                             title={"text": "Monthly Loss Trend by Cause", "font": {"color": "#ccc", "size": 13}})
    fig_trend.update_xaxes(tickangle=-30)

    return html.Div([
        page_header("Shrinkage & Loss",
                    "Theft, damage, expiry and admin errors — where inventory value disappears",
                    "fa-triangle-exclamation"),
        html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_cause, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_store, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_trend, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px"}),
        ], style={"padding": "20px 28px"})
    ])
