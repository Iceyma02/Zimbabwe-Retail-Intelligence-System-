"""Map View — Page 2 with Retailer Filter and Store Logos"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/map", name="Map View", order=1)

# Retailer logo mapping
RETAILER_LOGOS = {
    "PNP": "/assets/logos/pnp.png",
    "OK": "/assets/logos/ok.png",
    "SPAR": "/assets/logos/spar.png",
    "SAIMART": "/assets/logos/saimart.png",
    "CHOPPIES": "/assets/logos/choppies.png",
}

def layout():
    return html.Div([
        page_header("Map View", "All ZimRetail IQ store locations with live performance overlay", "fa-map-location-dot"),
        html.Div([
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
            html.Div([
                dcc.Graph(id="zimbabwe-map", config={"displayModeBar": False}, style={"height": "680px"})
            ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                      "borderRadius": "10px", "padding": "8px"})
        ], style={"display": "flex", "gap": "14px", "padding": "20px 28px"}),
    ])


@callback(
    Output("zimbabwe-map", "figure"),
    Output("map-store-cards", "children"),
    Input("map-color-by", "value"),
    Input("active-retailer", "data")
)
def update_map(color_by, retailer):
    df = get_store_revenue_summary(30, retailer)
    
    if df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            mapbox={"style": "carto-darkmatter", "center": {"lat": -19.0, "lon": 29.8}, "zoom": 5.5},
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"No stores found for {retailer}", x=0.5, y=0.5, showarrow=False, font=dict(color="#888"))]
        )
        return empty_fig, html.Div(f"No stores available for {retailer}", style={"color": "#888", "padding": "20px"})

    color_col = {"revenue": "total_revenue", "profit": "total_profit", "margin": "margin_pct"}[color_by]
    color_label = {"revenue": "Revenue ($)", "profit": "Profit ($)", "margin": "Margin (%)"}[color_by]

    df = df.sort_values(color_col, ascending=False).reset_index(drop=True)
    df["tier"] = df.index.map(lambda i: "🥇 Top" if i < 3 else ("🟡 Mid" if i < 6 else "🔴 Low"))
    df["size"] = df[color_col] / df[color_col].max() * 40 + 15 if df[color_col].max() > 0 else 20

    retailer_icons = {"PNP": "🛒", "OK": "🛍️", "SPAR": "🏪", "SAIMART": "🏬", "CHOPPIES": "🛒"}
    
    hover_text = df.apply(lambda r: (
        f"<b>{r['store_name']}</b><br>"
        f"Retailer: {retailer_icons.get(r.get('retailer_id', ''), '📍')} {r.get('retailer_id', 'N/A')}<br>"
        f"City: {r['city']}<br>"
        f"Revenue: ${r['total_revenue']:,.0f}<br>"
        f"Profit: ${r['total_profit']:,.0f}<br>"
        f"Margin: {r['margin_pct']:.1f}%<br>"
        f"Tier: {r['tier']}"
    ), axis=1)

    fig = go.Figure()
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

    # Create store cards with logos
    cards = []
    for _, row in df.iterrows():
        tier_color = {"🥇 Top": "#22c55e", "🟡 Mid": "#eab308", "🔴 Low": "#ef4444"}[row["tier"]]
        retailer_logo = RETAILER_LOGOS.get(row.get("retailer_id", ""))
        retailer_icon = retailer_icons.get(row.get("retailer_id", ""), "📍")
        
        # Check if logo exists
        logo_exists = False
        if retailer_logo:
            logo_path = os.path.join("assets", "logos", os.path.basename(retailer_logo))
            if os.path.exists(logo_path):
                logo_exists = True
        
        cards.append(html.Div([
            html.Div([
                # Logo or icon
                html.Img(src=retailer_logo, style={
                    "height": "20px", "width": "20px", "marginRight": "8px", "objectFit": "contain"
                }) if logo_exists else html.Span(retailer_icon, style={"fontSize": "14px", "marginRight": "8px"}),
                html.Span(row["tier"].split()[0], style={"fontSize": "14px"}),
                html.Div([
                    html.Div(row["store_name"], style={"color": "#ddd", "fontSize": "12px", "fontWeight": "500"}),
                    html.Div(row["city"], style={"color": "#666", "fontSize": "11px"})
                ], style={"flex": 1, "marginLeft": "8px"}),
                html.Div(f"${row['total_revenue']:,.0f}", style={"color": tier_color, "fontSize": "12px", "fontWeight": "700"})
            ], style={"display": "flex", "alignItems": "center"})
        ], style={"padding": "8px 12px", "borderBottom": "1px solid #1e1e1e",
                  "background": "#161616", "cursor": "pointer"}))

    retailer_name = retailer if retailer != "ALL" else "All Retailers"
    cards_container = html.Div([
        html.Div(f"Store Rankings — {retailer_name}", 
                 style={"color": "#888", "fontSize": "11px",
                        "textTransform": "uppercase", "letterSpacing": "1px",
                        "padding": "12px", "borderBottom": "1px solid #222"}),
        *cards
    ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "overflow": "hidden"})

    return fig, cards_container
