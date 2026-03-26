"""Executive Reports — Page 17"""
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

dash.register_page(__name__, path="/page-path", name="Page Name", order=0)

def layout():
    return html.Div([
        page_header("Executive Reports", "One-click board-ready summaries — PDF export for leadership", "fa-file-pdf"),
        html.Div([
            # Report config card
            html.Div([
                html.Div([
                    html.Div("📋 Report Configuration", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "16px"
                    }),
                    html.Div([
                        html.Div([
                            html.Label("Report Type", style={"color": "#888", "fontSize": "12px", "marginBottom": "6px", "display": "block"}),
                            dcc.Dropdown(
                                id="rpt-type",
                                options=[
                                    {"label": "📊 Monthly Executive Summary", "value": "monthly"},
                                    {"label": "🚨 Urgent Operations Alert", "value": "ops"},
                                    {"label": "💰 Financial Performance", "value": "finance"},
                                    {"label": "🔄 Supply Chain Status", "value": "supply"},
                                ],
                                value="monthly", clearable=False,
                                style={"width": "100%"}
                            )
                        ], style={"flex": 1}),
                        html.Div([
                            html.Label("Period", style={"color": "#888", "fontSize": "12px", "marginBottom": "6px", "display": "block"}),
                            dcc.Dropdown(
                                id="rpt-period",
                                options=[
                                    {"label": "Last 30 Days", "value": 30},
                                    {"label": "Last 60 Days", "value": 60},
                                    {"label": "Last 90 Days", "value": 90},
                                ],
                                value=30, clearable=False,
                                style={"width": "100%"}
                            )
                        ], style={"width": "160px"}),
                        html.Div([
                            html.Label("\u00a0", style={"display": "block", "marginBottom": "6px"}),
                            html.Button("🔄 Generate Report", id="rpt-generate-btn",
                                        style={
                                            "background": "#00c853", "color": "#fff",
                                            "border": "none", "borderRadius": "6px",
                                            "padding": "9px 20px", "cursor": "pointer",
                                            "fontFamily": "'DM Sans', sans-serif",
                                            "fontWeight": "600", "fontSize": "13px",
                                            "width": "100%"
                                        })
                        ], style={"width": "180px"}),
                    ], style={"display": "flex", "gap": "14px", "alignItems": "flex-end"})
                ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px",
                          "marginBottom": "20px"})
            ]),

            # Report preview area
            html.Div(id="rpt-preview")
        ], style={"padding": "20px 28px"})
    ])


def build_report_preview(report_type, days):
    """Build a beautiful HTML report preview"""
    kpis = get_national_kpis(days)
    store_rev = get_store_revenue_summary(days)
    inv = get_inventory_simple()
    credit = get_supplier_credit()
    economic = get_economic_indicators()

    revenue = kpis["total_revenue"].iloc[0] or 0
    profit = kpis["total_profit"].iloc[0] or 0
    margin = kpis["margin_pct"].iloc[0] or 0
    critical_stock = len(inv[inv["status"] == "CRITICAL"])
    low_stock = len(inv[inv["status"] == "LOW"])
    outstanding_debt = credit["outstanding_usd"].sum()
    stopped_suppliers = len(credit[credit["supplier_status"] == "STOPPED"]["supplier_name"].unique())
    latest_zig = economic["usd_zig_rate"].iloc[0] if not economic.empty else "N/A"
    latest_inflation = economic["inflation_rate_percent"].iloc[0] if not economic.empty else "N/A"

    top_store = store_rev.iloc[0] if not store_rev.empty else None
    bottom_store = store_rev.iloc[-1] if not store_rev.empty else None

    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")

    # Risk assessment
    risks = []
    if critical_stock > 10:
        risks.append(f"⚠️  {critical_stock} products at CRITICAL stock levels across all stores")
    if stopped_suppliers > 0:
        risks.append(f"🔴 {stopped_suppliers} supplier(s) have stopped trading due to outstanding payments")
    if outstanding_debt > 50000:
        risks.append(f"💳 Total supplier debt of ${outstanding_debt:,.0f} requires urgent attention")
    if margin < 12:
        risks.append(f"📉 National profit margin at {margin:.1f}% — below the 12% threshold")
    if not risks:
        risks.append("✅ No critical risks identified in this period")

    # Wins
    wins = []
    if margin > 15:
        wins.append(f"✅ Strong profit margin at {margin:.1f}%")
    if top_store is not None:
        wins.append(f"✅ {top_store['store_name']} leading with ${top_store['total_revenue']:,.0f} revenue")
    wins.append(f"✅ {9 - critical_stock // 5} of 9 stores operating at healthy stock levels")

    def metric_row(label, value, color="#fff"):
        return html.Div([
            html.Span(label, style={"color": "#888", "fontSize": "13px", "flex": 1}),
            html.Span(value, style={"color": color, "fontWeight": "700", "fontSize": "14px"})
        ], style={"display": "flex", "padding": "8px 0", "borderBottom": "1px solid #1e1e1e"})

    report = html.Div([
        # Report header
        html.Div([
            html.Div([
                html.Div([
                    html.Span("PnP", style={"color": "#00c853", "fontWeight": "800", "fontSize": "22px"}),
                    html.Span(" Zimbabwe", style={"color": "#fff", "fontSize": "18px"}),
                ]),
                html.Div("Retail Intelligence Platform — Executive Report",
                         style={"color": "#888", "fontSize": "12px"}),
            ]),
            html.Div([
                html.Div(f"Generated: {generated_at}", style={"color": "#666", "fontSize": "11px", "textAlign": "right"}),
                html.Div(f"Period: Last {days} days", style={"color": "#888", "fontSize": "11px", "textAlign": "right"}),
            ])
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                  "borderBottom": "2px solid #e31837", "paddingBottom": "16px", "marginBottom": "24px"}),

        # National KPIs
        html.Div([
            html.Div("NATIONAL PERFORMANCE", style={"color": "#00c853", "fontSize": "11px",
                                                      "textTransform": "uppercase", "letterSpacing": "1.5px",
                                                      "fontWeight": "700", "marginBottom": "14px"}),
            html.Div([
                html.Div([
                    html.Div(f"${revenue:,.0f}", style={"color": "#fff", "fontSize": "32px",
                                                         "fontWeight": "800", "fontFamily": "'Syne', sans-serif"}),
                    html.Div("Total Revenue", style={"color": "#888", "fontSize": "11px"})
                ], style={"flex": 1, "textAlign": "center", "padding": "16px",
                           "background": "#1a1a1a", "borderRadius": "8px", "border": "1px solid #e3183720"}),
                html.Div([
                    html.Div(f"${profit:,.0f}", style={"color": "#22c55e", "fontSize": "32px",
                                                        "fontWeight": "800", "fontFamily": "'Syne', sans-serif"}),
                    html.Div("Net Profit", style={"color": "#888", "fontSize": "11px"})
                ], style={"flex": 1, "textAlign": "center", "padding": "16px",
                           "background": "#1a1a1a", "borderRadius": "8px", "border": "1px solid #22c55e20"}),
                html.Div([
                    html.Div(f"{margin:.1f}%", style={
                        "color": "#22c55e" if margin > 15 else "#f97316" if margin > 10 else "#ef4444",
                        "fontSize": "32px", "fontWeight": "800", "fontFamily": "'Syne', sans-serif"
                    }),
                    html.Div("Profit Margin", style={"color": "#888", "fontSize": "11px"})
                ], style={"flex": 1, "textAlign": "center", "padding": "16px",
                           "background": "#1a1a1a", "borderRadius": "8px"}),
                html.Div([
                    html.Div("9", style={"color": "#3b82f6", "fontSize": "32px",
                                          "fontWeight": "800", "fontFamily": "'Syne', sans-serif"}),
                    html.Div("Active Stores", style={"color": "#888", "fontSize": "11px"})
                ], style={"flex": 1, "textAlign": "center", "padding": "16px",
                           "background": "#1a1a1a", "borderRadius": "8px"}),
            ], style={"display": "flex", "gap": "12px"})
        ], style={"marginBottom": "24px"}),

        # Two columns — Store ranking + Financial detail
        html.Div([
            html.Div([
                html.Div("STORE RANKINGS", style={"color": "#888", "fontSize": "11px",
                                                   "textTransform": "uppercase", "letterSpacing": "1px",
                                                   "marginBottom": "12px"}),
                *[metric_row(
                    f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else f'#{i+1}'} {row['store_name']}",
                    f"${row['total_revenue']:,.0f}",
                    "#22c55e" if i < 3 else "#fff"
                ) for i, (_, row) in enumerate(store_rev.iterrows())]
            ], style={"flex": 1, "background": "#1a1a1a", "borderRadius": "8px", "padding": "16px"}),

            html.Div([
                html.Div("FINANCIAL HEALTH", style={"color": "#888", "fontSize": "11px",
                                                      "textTransform": "uppercase", "letterSpacing": "1px",
                                                      "marginBottom": "12px"}),
                metric_row("Supplier Debt Outstanding", f"${outstanding_debt:,.0f}",
                            "#ef4444" if outstanding_debt > 50000 else "#f97316"),
                metric_row("Stopped Suppliers", str(stopped_suppliers),
                            "#ef4444" if stopped_suppliers > 0 else "#22c55e"),
                metric_row("Critical Stock Items", str(critical_stock),
                            "#ef4444" if critical_stock > 10 else "#eab308"),
                metric_row("Low Stock Items", str(low_stock), "#f97316"),
                metric_row("USD / ZiG Rate", str(latest_zig), "#eab308"),
                metric_row("Inflation Rate", f"{latest_inflation}%", "#ef4444"),
            ], style={"flex": 1, "background": "#1a1a1a", "borderRadius": "8px", "padding": "16px"}),
        ], style={"display": "flex", "gap": "14px", "marginBottom": "24px"}),

        # Risks & Wins
        html.Div([
            html.Div([
                html.Div("🚨 KEY RISKS", style={"color": "#ef4444", "fontSize": "12px",
                                                  "fontWeight": "700", "marginBottom": "12px"}),
                *[html.Div(r, style={"color": "#ddd", "fontSize": "13px", "padding": "6px 0",
                                      "borderBottom": "1px solid #2a2a2a"}) for r in risks]
            ], style={"flex": 1, "background": "#1a0808", "border": "1px solid #ef444430",
                       "borderRadius": "8px", "padding": "16px"}),

            html.Div([
                html.Div("✅ WINS THIS PERIOD", style={"color": "#22c55e", "fontSize": "12px",
                                                         "fontWeight": "700", "marginBottom": "12px"}),
                *[html.Div(w, style={"color": "#ddd", "fontSize": "13px", "padding": "6px 0",
                                      "borderBottom": "1px solid #2a2a2a"}) for w in wins]
            ], style={"flex": 1, "background": "#0a1a0a", "border": "1px solid #22c55e30",
                       "borderRadius": "8px", "padding": "16px"}),
        ], style={"display": "flex", "gap": "14px", "marginBottom": "24px"}),

        # Recommended Actions
        html.Div([
            html.Div("⚡ RECOMMENDED ACTIONS", style={"color": "#eab308", "fontSize": "12px",
                                                        "fontWeight": "700", "marginBottom": "12px"}),
            *[html.Div(f"{i+1}. {action}", style={"color": "#ddd", "fontSize": "13px",
                                                    "padding": "6px 0", "borderBottom": "1px solid #2a2a2a"})
              for i, action in enumerate([
                  f"Review and prioritise payment to {stopped_suppliers} stopped supplier(s) immediately",
                  f"Initiate emergency restock for {critical_stock} products at critical levels",
                  "Schedule weekly ZiG rate review — adjust pricing if rate exceeds 16.0",
                  "Run Christmas stock build-up analysis if approaching November/December",
                  "Review bottom-performing store operations for cost reduction opportunities"
              ])]
        ], style={"background": "#1a1500", "border": "1px solid #eab30830",
                  "borderRadius": "8px", "padding": "16px"}),

        # Footer
        html.Div([
            html.Div("This report was generated by ZimRetail IQ Retail Intelligence Platform",
                     style={"color": "#444", "fontSize": "11px", "textAlign": "center"}),
            html.Div("Data is simulated for portfolio demonstration purposes",
                     style={"color": "#333", "fontSize": "10px", "textAlign": "center", "marginTop": "4px"})
        ], style={"marginTop": "24px", "paddingTop": "16px", "borderTop": "1px solid #1e1e1e"})

    ], style={"background": "#111", "border": "1px solid #222", "borderRadius": "10px", "padding": "28px"})

    return report


@callback(
    Output("rpt-preview", "children"),
    Input("rpt-generate-btn", "n_clicks"),
    State("rpt-type", "value"),
    State("rpt-period", "value"),
    prevent_initial_call=False
)
def generate_report(n_clicks, report_type, days):
    return build_report_preview(report_type, days)
