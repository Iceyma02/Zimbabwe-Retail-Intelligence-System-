"""Stock Movement Intelligence — Page 6"""
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

dash.register_page(__name__, path="/stock-movement", name="Stock Movement", order=5)
def layout():
    df = get_sales(90)
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").astype(str)

    weekly = df.groupby("week").agg(revenue=("revenue","sum"), units=("units_sold","sum")).reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=weekly["week"], y=weekly["units"], name="Units Sold",
                           marker_color="#3b82f6", opacity=0.8))
    fig1.update_layout(**CHART_LAYOUT,
                        title={"text": "Weekly Stock Movement (Units Sold)", "font": {"color": "#ccc", "size": 13}})
    fig1.update_xaxes(tickangle=-45, nticks=12)

    cat_weekly = df.groupby(["week", "category"])["units_sold"].sum().reset_index()
    fig2 = px.line(cat_weekly, x="week", y="units_sold", color="category")
    fig2.update_layout(**CHART_LAYOUT,
                        title={"text": "Units Moved by Category (Weekly)", "font": {"color": "#ccc", "size": 13}})
    fig2.update_xaxes(nticks=8)

    store_cat = df.groupby(["store_name", "category"])["units_sold"].sum().reset_index()
    pivot = store_cat.pivot(index="store_name", columns="category", values="units_sold").fillna(0)
    fig3 = go.Figure(go.Heatmap(
        z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
        colorscale=[[0, "#0d0d0d"], [0.5, "#00c853"], [1, "#88ffbb"]],
        showscale=True
    ))
    fig3.update_layout(**CHART_LAYOUT,
                        title={"text": "Store × Category Sales Heatmap", "font": {"color": "#ccc", "size": 13}})

    return html.Div([
        page_header("Stock Movement Intelligence",
                    "Why is stock moving — sales, deliveries, damage, theft breakdown", "fa-arrow-trend-up"),
        html.Div([
            html.Div([dcc.Graph(figure=fig1, config={"displayModeBar": False}, style={"height": "320px"})],
                     style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px",
                            "padding": "16px", "marginBottom": "14px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig2, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                                "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig3, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                                "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px"}),
        ], style={"padding": "20px 28px"})
    ])
