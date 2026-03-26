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

dash.register_page(__name__, path="/map", name="Map View", order=1)

def layout():
    return html.Div([
        page_header("Map View", "All ZimRetail IQ store locations with live performance overlay", "fa-map-location-dot"),
        html.Div([
            # Controls
            html.Div([
                html.Div([
                    html.Label("Color stores by:", style={"color": "#888", "fontSize": "12px"}),
                    dcc.RadioItems(
                        id="map-color-by",
                        options=[
                            {"label": "  Revenue", "value": "revenue"},
                            {"label": "  Profit", "value": "profit"},
                            {"label": "  Margin %", "value": "margin"},
                        ],
                        value="revenue",
                        labelStyle={"display": "block", "color": "#ccc", "fontSize": "13px", "margin": "4px 0"},
                        inputStyle={"marginRight": "6px", "accentColor": "#00c853"}
                    )
                ], style={"background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px", "marginBottom": "14px"}),

                html.Div(id="map-store-cards")
            ], style={"width": "260px", "flexShrink": 0}),

            # Map
            html.Div([
                dcc.Graph(id="zimbabwe-map", config={"displayModeBar": False},
                          style={"height": "680px"})
            ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                      "borderRadius": "10px", "padding": "8px"})

        ], style={"display": "flex", "gap": "14px", "padding": "20px 28px"}),
    ])


@callback(
    Output("zimbabwe-map", "figure"),
    Output("map-store-cards", "children"),
    Input("map-color-by", "value")
)
def update_map(color_by):
    df = get_store_revenue_summary(30)

    color_col = {"revenue": "total_revenue", "profit": "total_profit", "margin": "margin_pct"}[color_by]
    color_label = {"revenue": "Revenue ($)", "profit": "Profit ($)", "margin": "Margin (%)"}[color_by]

    # Tier labels
    df = df.sort_values(color_col, ascending=False).reset_index(drop=True)
    df["tier"] = df.index.map(lambda i: "🥇 Top" if i < 3 else ("🟡 Mid" if i < 6 else "🔴 Low"))
    df["size"] = df[color_col] / df[color_col].max() * 40 + 15

    hover_text = df.apply(lambda r: (
        f"<b>{r['store_name']}</b><br>"
        f"City: {r['city']}<br>"
        f"Revenue: ${r['total_revenue']:,.0f}<br>"
        f"Profit: ${r['total_profit']:,.0f}<br>"
        f"Margin: {r['margin_pct']:.1f}%<br>"
        f"Tier: {r['tier']}"
    ), axis=1)

    fig = go.Figure()

    # Add scatter mapbox
    fig.add_trace(go.Scattermapbox(
        lat=df["lat"], lon=df["lng"],
        mode="markers+text",
        marker=go.scattermapbox.Marker(
            size=df["size"],
            color=df[color_col],
            colorscale=[[0, "#2d0a0a"], [0.5, "#00c853"], [1, "#ff6b8a"]],
            showscale=True,
            colorbar={"title": color_label, "titlefont": {"color": "#888"}, "tickfont": {"color": "#888"}},
            opacity=0.9
        ),
        text=df["store_name"].str.split().str[0],
        textfont={"color": "white", "size": 11},
        textposition="top center",
        hovertext=hover_text,
        hoverinfo="text"
    ))

    fig.update_layout(
        mapbox={
            "style": "carto-darkmatter",
            "center": {"lat": -19.0, "lon": 29.8},
            "zoom": 5.5
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        font={"color": "#aaa"}
    )

    # Store cards
    cards = []
    for _, row in df.iterrows():
        tier_color = {"🥇 Top": "#22c55e", "🟡 Mid": "#eab308", "🔴 Low": "#ef4444"}[row["tier"]]
        cards.append(html.Div([
            html.Div([
                html.Span(row["tier"].split()[0], style={"fontSize": "14px"}),
                html.Div([
                    html.Div(row["store_name"], style={"color": "#ddd", "fontSize": "12px", "fontWeight": "500"}),
                    html.Div(row["city"], style={"color": "#666", "fontSize": "11px"})
                ], style={"flex": 1, "marginLeft": "8px"}),
                html.Div(f"${row['total_revenue']:,.0f}", style={"color": tier_color, "fontSize": "12px", "fontWeight": "700"})
            ], style={"display": "flex", "alignItems": "center"})
        ], style={"padding": "8px 12px", "borderBottom": "1px solid #1e1e1e",
                  "background": "#161616", "cursor": "pointer"}))

    cards_container = html.Div([
        html.Div("Store Rankings", style={"color": "#888", "fontSize": "11px",
                                           "textTransform": "uppercase", "letterSpacing": "1px",
                                           "padding": "12px", "borderBottom": "1px solid #222"}),
        *cards
    ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "overflow": "hidden"})

    return fig, cards_container
