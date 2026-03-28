"""Executive Reports — Page 17 with PDF Preview & Print"""
import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/reports", name="Executive Reports", order=16)

def layout():
    return html.Div([
        page_header("Executive Reports", "One-click board-ready summaries — Print to PDF for leadership", "fa-file-pdf"),
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
                            html.Button("🔄 Generate Preview", id="rpt-generate-btn",
                                        style={
                                            "background": "#00c853", "color": "#fff",
                                            "border": "none", "borderRadius": "6px",
                                            "padding": "9px 20px", "cursor": "pointer",
                                            "fontFamily": "'DM Sans', sans-serif",
                                            "fontWeight": "600", "fontSize": "13px",
                                            "width": "100%"
                                        })
                        ], style={"width": "180px"}),
                        html.Div([
                            html.Label("\u00a0", style={"display": "block", "marginBottom": "6px"}),
                            html.Button("🖨️ Save as PDF", id="rpt-print-btn",
                                        style={
                                            "background": "#3b82f6", "color": "#fff",
                                            "border": "none", "borderRadius": "6px",
                                            "padding": "9px 20px", "cursor": "pointer",
                                            "fontFamily": "'DM Sans', sans-serif",
                                            "fontWeight": "600", "fontSize": "13px",
                                            "width": "100%"
                                        })
                        ], style={"width": "180px"}),
                    ], style={"display": "flex", "gap": "14px", "alignItems": "flex-end", "flexWrap": "wrap"}),
                ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px",
                          "marginBottom": "20px"})
            ]),
            # Report preview area
            html.Div(id="rpt-preview", style={"minHeight": "400px"}),
            # Hidden iframe for printing
            html.Iframe(id="rpt-print-iframe", style={"display": "none"}),
        ], style={"padding": "20px 28px"})
    ])


def build_report_preview(report_type, days, retailer):
    """Build a beautiful HTML report preview"""
    try:
        # Get data
        kpis = get_national_kpis(days, retailer)
        store_rev = get_store_revenue_summary(days, retailer)
        inv = get_inventory_simple(retailer)
        credit = get_supplier_credit()
        economic = get_economic_indicators()

        revenue = kpis["total_revenue"].iloc[0] if not kpis.empty else 0
        profit = kpis["total_profit"].iloc[0] if not kpis.empty else 0
        margin = kpis["margin_pct"].iloc[0] if not kpis.empty else 0
        critical_stock = len(inv[inv["status"] == "CRITICAL"]) if not inv.empty else 0
        low_stock = len(inv[inv["status"] == "LOW"]) if not inv.empty else 0
        outstanding_debt = credit["outstanding_usd"].sum() if not credit.empty else 0
        stopped_suppliers = len(credit[credit["supplier_status"] == "STOPPED"]["supplier_name"].unique()) if not credit.empty else 0
        latest_zig = economic["usd_zig_rate"].iloc[0] if not economic.empty else "N/A"
        latest_inflation = economic["inflation_rate_percent"].iloc[0] if not economic.empty else "N/A"

        top_store = store_rev.iloc[0] if not store_rev.empty else None

        generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")
        retailer_name = retailer if retailer != "ALL" else "All Retailers"

        # Report type specific content
        report_title = ""
        if report_type == "monthly":
            report_title = "Monthly Executive Summary"
        elif report_type == "ops":
            report_title = "Urgent Operations Alert"
        elif report_type == "finance":
            report_title = "Financial Performance Report"
        elif report_type == "supply":
            report_title = "Supply Chain Status Report"

        # Risks assessment
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

        # Create store ranking items safely
        store_ranking_items = []
        if not store_rev.empty:
            for i, (_, row) in enumerate(store_rev.iterrows()):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                store_ranking_items.append(metric_row(
                    f"{medal} {row['store_name']}",
                    f"${row['total_revenue']:,.0f}",
                    "#22c55e" if i < 3 else "#fff"
                ))
        else:
            store_ranking_items.append(html.Div("No store data", style={"color": "#888"}))

        report = html.Div([
            # Report header
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("ZimRetail", style={"color": "#00c853", "fontWeight": "800", "fontSize": "28px"}),
                        html.Span(" IQ", style={"color": "#fff", "fontSize": "28px"}),
                    ]),
                    html.Div(f"Retail Intelligence Platform — {report_title}", style={"color": "#888", "fontSize": "12px"}),
                ]),
                html.Div([
                    html.Div(f"Generated: {generated_at}", style={"color": "#666", "fontSize": "11px", "textAlign": "right"}),
                    html.Div(f"Period: Last {days} days", style={"color": "#888", "fontSize": "11px", "textAlign": "right"}),
                    html.Div(f"Retailer: {retailer_name}", style={"color": "#888", "fontSize": "11px", "textAlign": "right"}),
                ])
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                      "borderBottom": "2px solid #e31837", "paddingBottom": "20px", "marginBottom": "24px"}),

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
                        html.Div(str(len(store_rev)) if not store_rev.empty else "0", 
                                 style={"color": "#3b82f6", "fontSize": "32px",
                                        "fontWeight": "800", "fontFamily": "'Syne', sans-serif"}),
                        html.Div("Active Stores", style={"color": "#888", "fontSize": "11px"})
                    ], style={"flex": 1, "textAlign": "center", "padding": "16px",
                               "background": "#1a1a1a", "borderRadius": "8px"}),
                ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap"})
            ], style={"marginBottom": "24px"}),

            # Two columns
            html.Div([
                html.Div([
                    html.Div("STORE RANKINGS", style={"color": "#888", "fontSize": "11px",
                                                       "textTransform": "uppercase", "letterSpacing": "1px",
                                                       "marginBottom": "12px"}),
                    *store_ranking_items
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
            ], style={"display": "flex", "gap": "14px", "marginBottom": "24px", "flexWrap": "wrap"}),

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
            ], style={"display": "flex", "gap": "14px", "marginBottom": "24px", "flexWrap": "wrap"}),

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
        
    except Exception as e:
        print(f"Error building report: {e}")
        return html.Div([
            html.Div("⚠️ Error Generating Report", style={
                "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
            }),
            html.Div(str(e), style={"color": "#888", "fontSize": "14px"})
        ], style={"textAlign": "center", "padding": "60px", "background": "#111", "borderRadius": "10px"})


@callback(
    Output("rpt-preview", "children"),
    Input("rpt-generate-btn", "n_clicks"),
    State("rpt-type", "value"),
    State("rpt-period", "value"),
    State("active-retailer", "data"),
    prevent_initial_call=False
)
def generate_preview(n_clicks, report_type, days, retailer):
    """Generate report preview"""
    return build_report_preview(report_type, days, retailer)


@callback(
    Output("rpt-print-iframe", "srcDoc"),
    Input("rpt-print-btn", "n_clicks"),
    State("rpt-type", "value"),
    State("rpt-period", "value"),
    State("active-retailer", "data"),
    prevent_initial_call=True
)
def print_report(n_clicks, report_type, days, retailer):
    """Generate printable version and trigger print"""
    if n_clicks is None:
        return ""
    
    # Generate the report content
    report_content = build_report_preview(report_type, days, retailer)
    
    # Convert to string for iframe
    from dash import html as dash_html
    content_str = dash_html.Div(report_content).to_string()
    
    # Create HTML document for printing with print styles
    print_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ZimRetail IQ Report</title>
        <style>
            @media print {{
                body {{
                    background: white;
                    margin: 1cm;
                    font-family: 'DM Sans', 'Segoe UI', Arial, sans-serif;
                }}
                .no-print {{
                    display: none;
                }}
                @page {{
                    size: A4;
                    margin: 1.5cm;
                }}
            }}
            body {{
                background: #0d0d0d;
                font-family: 'DM Sans', 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #ddd;
            }}
            .report-container {{
                max-width: 1200px;
                margin: 0 auto;
                background: #111;
                border: 1px solid #222;
                border-radius: 10px;
                padding: 28px;
            }}
            button {{
                display: none;
            }}
            @media print {{
                .report-container {{
                    background: white;
                    border: none;
                    padding: 0;
                    margin: 0;
                }}
                * {{
                    color: black !important;
                }}
                .bg-dark {{
                    background: white !important;
                }}
                [style*="background: #1a1a1a"] {{
                    background: #f5f5f5 !important;
                }}
                [style*="border: 1px solid"] {{
                    border-color: #ddd !important;
                }}
            }}
        </style>
        <script>
            window.onload = function() {{
                setTimeout(function() {{
                    window.print();
                }}, 500);
            }}
        </script>
    </head>
    <body>
        <div class="report-container">
            {content_str}
        </div>
    </body>
    </html>
    """
    
    return print_html
