"""
ZimRetail IQ — Zimbabwe Retail Intelligence Platform
Generic multi-retailer analytics system
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import os

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="ZimRetail IQ — Retail Intelligence Platform"
)

server = app.server

RETAILERS = [
    {"label": "📍 All Retailers",     "value": "ALL",     "color": "#00c853"},
    {"label": "🛒 TM Pick n Pay",     "value": "PNP",     "color": "#e31837"},
    {"label": "🛍️  OK Zimbabwe",       "value": "OK",      "color": "#ff6d00"},
    {"label": "🏪 Spar Zimbabwe",      "value": "SPAR",    "color": "#007b40"},
    {"label": "🏬 SaiMart",           "value": "SAIMART", "color": "#1565c0"},
    {"label": "🛒 Choppies Zimbabwe",  "value": "CHOPPIES","color": "#f9a825"},
]

NAV_ITEMS = [
    {"icon": "fa-gauge-high",          "label": "National Overview",    "href": "/"},
    {"icon": "fa-map-location-dot",    "label": "Map View",             "href": "/map"},
    {"icon": "fa-chart-bar",           "label": "Store Performance",    "href": "/performance"},
    {"icon": "fa-coins",               "label": "Store P&L",            "href": "/pnl"},
    {"icon": "fa-boxes-stacked",       "label": "Inventory Monitor",    "href": "/inventory"},
    {"icon": "fa-arrow-trend-up",      "label": "Stock Movement",       "href": "/stock-movement"},
    {"icon": "fa-brain",               "label": "Demand Forecasting",   "href": "/forecasting"},
    {"icon": "fa-rotate",              "label": "Reorder Optimizer",    "href": "/reorder"},
    {"icon": "fa-truck-fast",          "label": "Supply Chain",         "href": "/supply-chain"},
    {"icon": "fa-file-invoice-dollar", "label": "Supplier Credit",      "href": "/supplier-credit"},
    {"icon": "fa-tags",                "label": "Promotions ROI",       "href": "/promotions"},
    {"icon": "fa-store",               "label": "Competitor Watch",     "href": "/competitor"},
    {"icon": "fa-face-smile",          "label": "Customer Sentiment",   "href": "/sentiment"},
    {"icon": "fa-users",               "label": "Workforce",            "href": "/workforce"},
    {"icon": "fa-triangle-exclamation","label": "Shrinkage & Loss",     "href": "/shrinkage"},
    {"icon": "fa-globe-africa",        "label": "Market Watch",         "href": "/market-watch"},
    {"icon": "fa-file-pdf",            "label": "Executive Reports",    "href": "/reports"},
]

sidebar = html.Div([
    html.Div([
        html.Div([
            html.Div("⚡", style={
                "width": "36px", "height": "36px", "borderRadius": "9px",
                "background": "linear-gradient(135deg, #00c853, #007b40)",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "fontSize": "18px", "marginRight": "10px", "flexShrink": "0"
            }),
            html.Div([
                html.Div([
                    html.Span("ZimRetail", style={"color": "#00c853", "fontWeight": "800",
                                                   "fontSize": "17px", "fontFamily": "'Syne', sans-serif"}),
                    html.Span(" IQ", style={"color": "#fff", "fontWeight": "300", "fontSize": "17px"}),
                ]),
                html.Div("Zimbabwe Retail Intelligence", style={
                    "color": "#555", "fontSize": "9px", "letterSpacing": "1.2px",
                    "textTransform": "uppercase", "marginTop": "-1px"
                })
            ])
        ], style={"display": "flex", "alignItems": "center"})
    ], style={"padding": "18px 14px 14px", "borderBottom": "1px solid #1e1e1e"}),

    html.Div([
        html.Div("Active Retailer", style={"color": "#555", "fontSize": "9px",
                                            "textTransform": "uppercase", "letterSpacing": "1px",
                                            "marginBottom": "6px"}),
        dcc.Dropdown(
            id="retailer-switcher",
            options=[{"label": r["label"], "value": r["value"]} for r in RETAILERS],
            value="ALL", clearable=False,
            style={"fontSize": "12px"}
        ),
    ], style={"padding": "10px 10px 10px", "borderBottom": "1px solid #1e1e1e"}),

    html.Div([
        dcc.Link([
            html.I(className=f"fa-solid {item['icon']}",
                   style={"width": "17px", "marginRight": "9px", "fontSize": "12px"}),
            html.Span(item["label"], style={"fontSize": "12.5px"})
        ],
        href=item["href"], className="sidebar-link",
        style={"display": "flex", "alignItems": "center", "padding": "8px 13px",
               "color": "#999", "textDecoration": "none", "borderRadius": "5px",
               "margin": "1px 7px", "transition": "all 0.15s", "borderLeft": "3px solid transparent"})
        for item in NAV_ITEMS
    ], style={"overflowY": "auto", "flex": "1", "paddingTop": "6px", "paddingBottom": "6px"}),

    html.Div([
        html.Div("Simulated data — portfolio project",
                 style={"color": "#333", "fontSize": "10px", "textAlign": "center"}),
        html.Div("Built by Anesu Manjengwa 🇿🇼",
                 style={"color": "#3a3a3a", "fontSize": "10px", "textAlign": "center", "marginTop": "2px"})
    ], style={"padding": "10px 12px", "borderTop": "1px solid #1a1a1a"})

], id="sidebar", style={
    "width": "232px", "minHeight": "100vh", "background": "#0e0e0e",
    "display": "flex", "flexDirection": "column",
    "position": "fixed", "top": 0, "left": 0, "zIndex": 1000,
    "fontFamily": "'DM Sans', sans-serif", "borderRight": "1px solid #1a1a1a"
})

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="active-retailer", data="ALL"),
    sidebar,
    html.Div([
        html.Div(id="retailer-banner"),
        dash.page_container
    ], style={
        "marginLeft": "232px", "minHeight": "100vh",
        "background": "#0d0d0d", "fontFamily": "'DM Sans', sans-serif"
    })
], style={"background": "#0d0d0d"})


app.clientside_callback(
    """
    function(pathname) {
        const links = document.querySelectorAll('.sidebar-link');
        links.forEach(link => {
            const href = link.getAttribute('href');
            const isActive = href === pathname || (pathname === '/' && href === '/');
            link.style.color = isActive ? '#fff' : '#999';
            link.style.background = isActive ? 'rgba(0,200,83,0.12)' : 'transparent';
            link.style.borderLeft = isActive ? '3px solid #00c853' : '3px solid transparent';
        });
        return '';
    }
    """,
    Output("url", "search"),
    Input("url", "pathname")
)


@app.callback(
    Output("retailer-banner", "children"),
    Output("active-retailer", "data"),
    Input("retailer-switcher", "value")
)
def update_retailer_banner(retailer_val):
    retailer = next((r for r in RETAILERS if r["value"] == retailer_val), RETAILERS[0])
    color = retailer["color"]
    if retailer_val == "ALL":
        return html.Div(), retailer_val
    banner = html.Div([
        html.Span(retailer["label"],
                  style={"color": color, "fontWeight": "700", "fontSize": "12px"}),
        html.Span(" · Showing data for this retailer's stores",
                  style={"color": "#555", "fontSize": "11px", "marginLeft": "8px"}),
    ], style={
        "background": f"{color}0d", "borderBottom": f"1px solid {color}20",
        "padding": "7px 28px", "display": "flex", "alignItems": "center"
    })
    return banner, retailer_val


if __name__ == "__main__":
    import os
    # Check if database exists, generate if not
    db_path = "data/zimretail_iq.db"
    if not os.path.exists(db_path):
        print("⚠️  Database not found. Running data generator first...")
        from data.generate_data import save_to_sqlite
        save_to_sqlite()
    app.run(debug=True, port=8050)
