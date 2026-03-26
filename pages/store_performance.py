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

dash.register_page(__name__, path="/page-path", name="Page Name", order=0)

def layout():
    return html.Div([
        page_header("Store Performance", "Revenue, profit and growth rankings across all stores", "fa-chart-bar"),
        html.Div([
            html.Div([
                html.Label("Time Period:", style={"color": "#888", "fontSize": "12px"}),
                dcc.Dropdown(
                    id="perf-period",
                    options=[{"label": "Last 30 Days", "value": 30},
                             {"label": "Last 60 Days", "value": 60},
                             {"label": "Last 90 Days", "value": 90}],
                    value=30, clearable=False,
                    style={"background": "#1e1e1e", "color": "#fff", "border": "1px solid #333", "width": "180px"}
                )
            ], style={"display": "flex", "alignItems": "center", "gap": "12px",
                      "marginBottom": "20px"}),

            # Revenue bar chart
            html.Div([
                dcc.Graph(id="perf-revenue-bar", config={"displayModeBar": False}, style={"height": "300px"})
            ], style={"background": "#161616", "border": "1px solid #222",
                      "borderRadius": "10px", "padding": "16px", "marginBottom": "14px"}),

            html.Div([
                html.Div([
                    dcc.Graph(id="perf-margin-chart", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
                html.Div([
                    dcc.Graph(id="perf-scatter", config={"displayModeBar": False}, style={"height": "260px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),

            # Table
            html.Div([
                html.Div("Full Store Performance Table", style={
                    "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                    "letterSpacing": "1px", "marginBottom": "14px"
                }),
                html.Div(id="perf-table")
            ], style={"background": "#161616", "border": "1px solid #222",
                      "borderRadius": "10px", "padding": "20px"})

        ], style={"padding": "20px 28px"})
    ])


@callback(
    Output("perf-revenue-bar", "figure"),
    Output("perf-margin-chart", "figure"),
    Output("perf-scatter", "figure"),
    Output("perf-table", "children"),
    Input("perf-period", "value")
)
def update_performance(days):
    df = get_store_revenue_summary(days)
    df = df.sort_values("total_revenue", ascending=False)

    # Revenue bar
    fig_bar = go.Figure(go.Bar(
        x=df["store_name"], y=df["total_revenue"],
        marker_color=["#00c853" if i < 3 else "#3b82f6" if i < 6 else "#555" for i in range(len(df))],
        text=df["total_revenue"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside", textfont={"color": "#aaa", "size": 11}
    ))
    fig_bar.update_layout(**CHART_LAYOUT, title={"text": f"Revenue by Store — Last {days} Days", "font": {"color": "#ccc", "size": 13}})

    # Margin chart
    df_sorted_margin = df.sort_values("margin_pct", ascending=True)
    fig_margin = go.Figure(go.Bar(
        x=df_sorted_margin["margin_pct"], y=df_sorted_margin["store_name"],
        orientation="h",
        marker_color=["#22c55e" if m > 18 else "#f97316" if m > 12 else "#ef4444"
                      for m in df_sorted_margin["margin_pct"]],
        text=df_sorted_margin["margin_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside"
    ))
    fig_margin.update_layout(**CHART_LAYOUT, title={"text": "Profit Margin % by Store", "font": {"color": "#ccc", "size": 13}})

    # Scatter — revenue vs profit
    fig_scatter = px.scatter(
        df, x="total_revenue", y="total_profit",
        size="total_units", color="margin_pct",
        text="store_name",
        color_continuous_scale=["#ef4444", "#eab308", "#22c55e"],
        size_max=40
    )
    fig_scatter.update_traces(textposition="top center", textfont={"size": 10, "color": "#aaa"})
    fig_scatter.update_layout(**CHART_LAYOUT, coloraxis_showscale=False,
                               title={"text": "Revenue vs Profit (bubble = units)", "font": {"color": "#ccc", "size": 13}})

    # Table
    headers = ["Store", "City", "Revenue", "Profit", "Units", "Margin", "Rank"]
    header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 12px",
                                             "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                          for h in headers])
    rows = []
    for rank, (_, row) in enumerate(df.iterrows(), 1):
        medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"#{rank}"
        m = row["margin_pct"] or 0
        margin_color = "#22c55e" if m > 18 else "#f97316" if m > 12 else "#ef4444"
        rows.append(html.Tr([
            html.Td(row["store_name"], style={"color": "#ddd", "padding": "8px 12px", "fontSize": "13px"}),
            html.Td(row["city"], style={"color": "#888", "padding": "8px 12px", "fontSize": "12px"}),
            html.Td(f"${row['total_revenue']:,.0f}", style={"color": "#fff", "padding": "8px 12px", "fontWeight": "600"}),
            html.Td(f"${row['total_profit']:,.0f}", style={"color": "#22c55e", "padding": "8px 12px"}),
            html.Td(f"{row['total_units']:,}", style={"color": "#888", "padding": "8px 12px"}),
            html.Td(f"{m:.1f}%", style={"color": margin_color, "padding": "8px 12px", "fontWeight": "600"}),
            html.Td(medal, style={"padding": "8px 12px", "fontSize": "14px"}),
        ], style={"borderBottom": "1px solid #1a1a1a"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width": "100%", "borderCollapse": "collapse"})
    return fig_bar, fig_margin, fig_scatter, table
