import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/", name="National Overview", order=0)

def layout():
    kpis = get_national_kpis(30)
    kpis_prev = get_national_kpis(60)
    revenue = kpis["total_revenue"].iloc[0] or 0
    profit = kpis["total_profit"].iloc[0] or 0
    units = kpis["total_units"].iloc[0] or 0
    margin = kpis["margin_pct"].iloc[0] or 0
    prev_revenue = kpis_prev["total_revenue"].iloc[0] or 1
    rev_delta = ((revenue - prev_revenue/2) / (prev_revenue/2)) * 100

    inv = get_inventory_simple()
    critical_count = len(inv[inv["status"] == "CRITICAL"])
    low_count = len(inv[inv["status"] == "LOW"])

    return html.Div([
        page_header("National Overview", "Real-time performance across all 12 Zimbabwe stores", "fa-gauge-high"),
        html.Div([
            # KPI Row
            html.Div([
                html.Div(kpi_card("30-Day Revenue", f"${revenue:,.0f}", rev_delta, "vs prev 30d", "fa-dollar-sign", "#00c853"), style={"flex": 1}),
                html.Div(kpi_card("30-Day Profit", f"${profit:,.0f}", None, None, "fa-chart-line", "#22c55e"), style={"flex": 1}),
                html.Div(kpi_card("Profit Margin", f"{margin:.1f}%", None, None, "fa-percent", "#3b82f6"), style={"flex": 1}),
                html.Div(kpi_card("Units Sold", f"{units:,}", None, None, "fa-box", "#8b5cf6"), style={"flex": 1}),
                html.Div(kpi_card("Critical Stock", str(critical_count), None, None, "fa-triangle-exclamation", "#ef4444"), style={"flex": 1}),
                html.Div(kpi_card("Low Stock Items", str(low_count), None, None, "fa-exclamation", "#f97316"), style={"flex": 1}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),

            # Charts row
            html.Div([
                # Revenue trend
                html.Div([
                    dcc.Graph(id="overview-trend", config={"displayModeBar": False},
                              style={"height": "260px"})
                ], style={"flex": "2", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),

                # Category breakdown
                html.Div([
                    dcc.Graph(id="overview-category", config={"displayModeBar": False},
                              style={"height": "260px"})
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),

            # Store leaderboard + alerts
            html.Div([
                # Store ranking
                html.Div([
                    html.Div("Store Revenue Ranking — Last 30 Days", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    html.Div(id="store-ranking-list")
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "20px"}),

                # Active alerts
                html.Div([
                    html.Div("🚨 Active Alerts", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    html.Div(id="active-alerts")
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "20px"}),
            ], style={"display": "flex", "gap": "14px"}),

        ], style={"padding": "20px 28px"}),

        dcc.Interval(id="overview-refresh", interval=300000, n_intervals=0)
    ])


@callback(Output("overview-trend", "figure"), Input("overview-refresh", "n_intervals"))
def update_trend(_):
    df = get_daily_trend(60)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["revenue"], name="Revenue",
        line={"color": "#00c853", "width": 2},
        fill="tozeroy", fillcolor="rgba(227,24,55,0.08)"
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["profit"], name="Profit",
        line={"color": "#22c55e", "width": 2}
    ))
    fig.update_layout(**CHART_LAYOUT, title={"text": "60-Day Revenue & Profit Trend", "font": {"color": "#ccc", "size": 13}})
    return fig


@callback(Output("overview-category", "figure"), Input("overview-refresh", "n_intervals"))
def update_category(_):
    df = get_category_sales(30)
    fig = px.bar(df, x="revenue", y="category", orientation="h",
                 color="revenue", color_continuous_scale=["#2d0a0a", "#00c853"])
    fig.update_layout(**CHART_LAYOUT, title={"text": "Revenue by Category", "font": {"color": "#ccc", "size": 13}},
                      showlegend=False, coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    return fig


@callback(Output("store-ranking-list", "children"), Input("overview-refresh", "n_intervals"))
def update_ranking(_):
    df = get_store_revenue_summary(30)
    items = []
    for i, row in df.iterrows():
        rank = list(df.index).index(i) + 1
        medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
        pct = row["margin_pct"] or 0
        items.append(html.Div([
            html.Span(medal, style={"fontSize": "16px", "width": "28px"}),
            html.Div([
                html.Div(row["store_name"], style={"color": "#ddd", "fontSize": "13px", "fontWeight": "500"}),
                html.Div(row["city"], style={"color": "#666", "fontSize": "11px"})
            ], style={"flex": 1}),
            html.Div([
                html.Div(f"${row['total_revenue']:,.0f}", style={"color": "#fff", "fontSize": "13px", "fontWeight": "600", "textAlign": "right"}),
                html.Div(f"{pct:.1f}% margin", style={"color": "#22c55e" if pct > 15 else "#f97316", "fontSize": "11px", "textAlign": "right"})
            ])
        ], style={"display": "flex", "alignItems": "center", "gap": "10px",
                  "padding": "8px 0", "borderBottom": "1px solid #1e1e1e"}))
    return items


@callback(Output("active-alerts", "children"), Input("overview-refresh", "n_intervals"))
def update_alerts(_):
    inv = get_inventory_simple()
    critical = inv[inv["status"] == "CRITICAL"].head(6)
    credit = get_supplier_credit()
    stopped = credit[credit["supplier_status"] == "STOPPED"]

    alerts = []
    for _, row in critical.iterrows():
        alerts.append(html.Div([
            html.Span("🔴", style={"marginRight": "8px"}),
            html.Div([
                html.Div(f"{row['product_name'][:28]}", style={"color": "#ddd", "fontSize": "12px"}),
                html.Div(f"{row['store_name']} — {row['current_stock']} units left",
                         style={"color": "#666", "fontSize": "11px"})
            ])
        ], style={"display": "flex", "alignItems": "center", "padding": "6px 0",
                  "borderBottom": "1px solid #1e1e1e"}))

    for _, row in stopped.head(3).iterrows():
        alerts.append(html.Div([
            html.Span("⛔", style={"marginRight": "8px"}),
            html.Div([
                html.Div(f"{row['supplier_name']} — STOPPED", style={"color": "#ef4444", "fontSize": "12px"}),
                html.Div(f"${row['outstanding_usd']:,.0f} outstanding",
                         style={"color": "#666", "fontSize": "11px"})
            ])
        ], style={"display": "flex", "alignItems": "center", "padding": "6px 0",
                  "borderBottom": "1px solid #1e1e1e"}))

    return alerts if alerts else [html.Div("✅ No critical alerts", style={"color": "#22c55e"})]
