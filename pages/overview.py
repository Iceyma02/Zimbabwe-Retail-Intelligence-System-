"""National Overview - Page 1"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db import (
    get_national_kpis, get_category_sales, get_daily_trend, 
    get_store_revenue_summary, get_inventory_simple, get_supplier_credit
)
from components.shared import page_header, kpi_card, status_badge, CHART_LAYOUT

dash.register_page(__name__, path="/", name="National Overview", order=0)

def layout():
    """Layout for national overview page"""
    return html.Div([
        page_header("National Overview", "Real-time performance across all Zimbabwe stores", "fa-gauge-high"),
        html.Div([
            # KPI Row - will be filled by callbacks
            html.Div(id="overview-kpis", style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            
            # Charts row
            html.Div([
                html.Div([
                    dcc.Graph(id="overview-trend", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": "2", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="overview-category", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            
            # Store leaderboard + alerts
            html.Div([
                html.Div([
                    html.Div("Store Revenue Ranking — Last 30 Days", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    html.Div(id="store-ranking-list")
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
                html.Div([
                    html.Div("🚨 Active Alerts", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    html.Div(id="active-alerts")
                ], style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
            ], style={"display": "flex", "gap": "14px"}),
        ], style={"padding": "20px 28px"}),
        dcc.Interval(id="overview-refresh", interval=300000, n_intervals=0)
    ])


@callback(
    Output("overview-kpis", "children"),
    Input("overview-refresh", "n_intervals")
)
def update_kpis(_):
    """Update KPI cards"""
    try:
        kpis = get_national_kpis(30)
        if kpis.empty:
            revenue = profit = units = margin = 0
        else:
            revenue = kpis["total_revenue"].iloc[0] if not kpis.empty else 0
            profit = kpis["total_profit"].iloc[0] if not kpis.empty else 0
            units = kpis["total_units"].iloc[0] if not kpis.empty else 0
            margin = kpis["margin_pct"].iloc[0] if not kpis.empty else 0
        
        # Get previous period for comparison
        kpis_prev = get_national_kpis(60)
        if kpis_prev.empty:
            prev_revenue = revenue
        else:
            prev_revenue = kpis_prev["total_revenue"].iloc[0] if not kpis_prev.empty else revenue
        
        rev_delta = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Inventory alerts
        inv = get_inventory_simple()
        critical_count = len(inv[inv["status"] == "CRITICAL"]) if not inv.empty else 0
        low_count = len(inv[inv["status"] == "LOW"]) if not inv.empty else 0
        
        return [
            html.Div(kpi_card("30-Day Revenue", f"${revenue:,.0f}", rev_delta, "vs prev 30d", "fa-dollar-sign", "#00c853"), style={"flex": 1}),
            html.Div(kpi_card("30-Day Profit", f"${profit:,.0f}", None, None, "fa-chart-line", "#22c55e"), style={"flex": 1}),
            html.Div(kpi_card("Profit Margin", f"{margin:.1f}%", None, None, "fa-percent", "#3b82f6"), style={"flex": 1}),
            html.Div(kpi_card("Units Sold", f"{units:,.0f}", None, None, "fa-box", "#8b5cf6"), style={"flex": 1}),
            html.Div(kpi_card("Critical Stock", str(critical_count), None, None, "fa-triangle-exclamation", "#ef4444"), style={"flex": 1}),
            html.Div(kpi_card("Low Stock Items", str(low_count), None, None, "fa-exclamation", "#f97316"), style={"flex": 1}),
        ]
    except Exception as e:
        print(f"Error updating KPIs: {e}")
        return [html.Div(f"Error loading data: {e}", style={"color": "#ef4444"})]


@callback(Output("overview-trend", "figure"), Input("overview-refresh", "n_intervals"))
def update_trend(_):
    """Update trend chart"""
    try:
        df = get_daily_trend(60)
        if df.empty:
            fig = go.Figure()
            fig.update_layout(**CHART_LAYOUT, title={"text": "No data available"})
            return fig
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["revenue"], name="Revenue",
            line={"color": "#00c853", "width": 2},
            fill="tozeroy", fillcolor="rgba(0,200,83,0.08)"
        ))
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["profit"], name="Profit",
            line={"color": "#22c55e", "width": 2}
        ))
        fig.update_layout(**CHART_LAYOUT, title={"text": "60-Day Revenue & Profit Trend", "font": {"color": "#ccc", "size": 13}})
        return fig
    except Exception as e:
        print(f"Error updating trend: {e}")
        fig = go.Figure()
        fig.update_layout(**CHART_LAYOUT, title={"text": f"Error: {e}"})
        return fig


@callback(Output("overview-category", "figure"), Input("overview-refresh", "n_intervals"))
def update_category(_):
    """Update category chart"""
    try:
        df = get_category_sales(30)
        if df.empty:
            fig = go.Figure()
            fig.update_layout(**CHART_LAYOUT, title={"text": "No data available"})
            return fig
        
        fig = px.bar(df, x="revenue", y="category", orientation="h",
                     color="revenue", color_continuous_scale=["#2d0a0a", "#00c853"])
        fig.update_layout(**CHART_LAYOUT, title={"text": "Revenue by Category", "font": {"color": "#ccc", "size": 13}},
                          showlegend=False, coloraxis_showscale=False)
        fig.update_traces(marker_line_width=0)
        return fig
    except Exception as e:
        print(f"Error updating category: {e}")
        fig = go.Figure()
        fig.update_layout(**CHART_LAYOUT, title={"text": f"Error: {e}"})
        return fig


@callback(Output("store-ranking-list", "children"), Input("overview-refresh", "n_intervals"))
def update_ranking(_):
    """Update store ranking"""
    try:
        df = get_store_revenue_summary(30)
        if df.empty:
            return html.Div("No store data available", style={"color": "#888"})
        
        items = []
        for i, (_, row) in enumerate(df.iterrows()):
            rank = i + 1
            medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
            pct = row["margin_pct"] if pd.notna(row["margin_pct"]) else 0
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
    except Exception as e:
        print(f"Error updating ranking: {e}")
        return html.Div(f"Error: {e}", style={"color": "#ef4444"})


@callback(Output("active-alerts", "children"), Input("overview-refresh", "n_intervals"))
def update_alerts(_):
    """Update alerts"""
    try:
        inv = get_inventory_simple()
        critical = inv[inv["status"] == "CRITICAL"].head(6) if not inv.empty else pd.DataFrame()
        credit = get_supplier_credit()
        stopped = credit[credit["supplier_status"] == "STOPPED"] if not credit.empty else pd.DataFrame()

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
    except Exception as e:
        print(f"Error updating alerts: {e}")
        return [html.Div(f"Error: {e}", style={"color": "#ef4444"})]
