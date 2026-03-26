"""Supplier Credit & Risk — Page 10"""
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

def compute_priority_score(row):
    status_score = {"STOPPED": 1.0, "LIMITED_CREDIT": 0.6, "ACTIVE": 0.1}.get(row["supplier_status"], 0.2)
    overdue_score = min(row["overdue_days"] / 60, 1.0)
    outstanding_pct = row["outstanding_usd"] / max(row["amount_usd"], 1)
    return round((0.3 * 0.4 + overdue_score * 0.3 + status_score * 0.2 + outstanding_pct * 0.1), 3)

def layout():
    df = get_supplier_credit()
    df["priority_score"] = df.apply(compute_priority_score, axis=1)
    df = df.sort_values("priority_score", ascending=False)

    active_count = len(df[df["supplier_status"] == "ACTIVE"]["supplier_name"].unique())
    limited_count = len(df[df["supplier_status"] == "LIMITED_CREDIT"]["supplier_name"].unique())
    stopped_count = len(df[df["supplier_status"] == "STOPPED"]["supplier_name"].unique())
    total_suppliers = active_count + limited_count + stopped_count
    confidence = int(((active_count * 1.0 + limited_count * 0.4) / max(total_suppliers, 1)) * 100)
    conf_color = "#22c55e" if confidence > 70 else "#eab308" if confidence > 45 else "#ef4444"

    confidence_block = html.Div([
        html.Div([
            html.Div([
                html.Div("SUPPLIER CONFIDENCE INDEX", style={"color": "#888", "fontSize": "11px", "letterSpacing": "1px"}),
                html.Div([
                    html.Span(f"{confidence}", style={"fontSize": "52px", "fontWeight": "800",
                                                        "color": conf_color, "fontFamily": "'Syne',sans-serif"}),
                    html.Span("/100", style={"color": "#444", "fontSize": "24px", "marginLeft": "4px"}),
                    html.Span(" ⚠️" if confidence < 70 else " ✅", style={"fontSize": "20px", "marginLeft": "8px"})
                ]),
            ]),
            html.Div([
                html.Div(f"✅ Actively trading: {active_count} suppliers", style={"color": "#22c55e", "fontSize": "13px", "margin": "4px 0"}),
                html.Div(f"⚠️  Limited credit: {limited_count} suppliers", style={"color": "#eab308", "fontSize": "13px", "margin": "4px 0"}),
                html.Div(f"❌ Stopped trading: {stopped_count} suppliers", style={"color": "#ef4444", "fontSize": "13px", "margin": "4px 0"}),
            ], style={"background": "#1a1a1a", "border": "1px solid #2a2a2a", "borderRadius": "8px", "padding": "12px 16px"})
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "40px"})
    ], style={"background": "#161616", "border": f"1px solid {conf_color}30",
              "borderLeft": f"4px solid {conf_color}", "borderRadius": "10px", "padding": "20px", "marginBottom": "20px"})

    total_outstanding = df["outstanding_usd"].sum()
    total_overdue = df[df["overdue_days"] > 0]["outstanding_usd"].sum()
    critical_suppliers = len(df[(df["supplier_status"] == "STOPPED") | (df["overdue_days"] > 30)]["supplier_name"].unique())

    kpis = [
        kpi_card("Total Outstanding", f"${total_outstanding:,.0f}", None, None, "fa-dollar-sign", "#00c853"),
        kpi_card("Overdue Amount", f"${total_overdue:,.0f}", None, None, "fa-clock", "#f97316"),
        kpi_card("At-Risk Suppliers", str(critical_suppliers), None, None, "fa-triangle-exclamation", "#ef4444"),
        kpi_card("Active Suppliers", str(active_count), None, None, "fa-handshake", "#22c55e"),
    ]

    # Status chart
    sup_status = df.groupby(["supplier_name", "supplier_status"])["outstanding_usd"].sum().reset_index()
    sup_status = sup_status.sort_values("outstanding_usd", ascending=False).head(14)
    status_color_map = {"ACTIVE": "#22c55e", "LIMITED_CREDIT": "#f97316", "STOPPED": "#ef4444"}
    fig_status = go.Figure()
    for status, color in status_color_map.items():
        sub = sup_status[sup_status["supplier_status"] == status]
        if not sub.empty:
            fig_status.add_trace(go.Bar(x=sub["outstanding_usd"], y=sub["supplier_name"],
                                         name=status.replace("_", " "), orientation="h", marker_color=color))
    fig_status.update_layout(**CHART_LAYOUT, barmode="stack",
                              title={"text": "Outstanding by Supplier & Status", "font": {"color": "#ccc", "size": 13}},
                              yaxis={"categoryorder": "total ascending"})

    # Aging
    bins = pd.cut(df["overdue_days"], bins=[-1, 0, 14, 30, 60, 999],
                  labels=["Current", "1-14d", "15-30d", "31-60d", "60d+"])
    age_amounts = df.groupby(bins)["outstanding_usd"].sum().reset_index()
    age_amounts.columns = ["bucket", "amount"]
    fig_aging = go.Figure(go.Bar(
        x=age_amounts["bucket"].astype(str), y=age_amounts["amount"],
        marker_color=["#22c55e", "#3b82f6", "#eab308", "#f97316", "#ef4444"]
    ))
    fig_aging.update_layout(**CHART_LAYOUT, title={"text": "Accounts Payable Aging", "font": {"color": "#ccc", "size": 13}})

    # Outstanding top 10
    top_out = df.groupby("supplier_name")["outstanding_usd"].sum().sort_values(ascending=False).head(10)
    fig_out = go.Figure(go.Bar(x=top_out.values, y=top_out.index, orientation="h", marker_color="#00c853"))
    fig_out.update_layout(**CHART_LAYOUT, title={"text": "Top 10 Outstanding Balances", "font": {"color": "#ccc", "size": 13}},
                           yaxis={"categoryorder": "total ascending"})

    # Priority table
    unique_suppliers = df.drop_duplicates("supplier_name").head(15)
    headers = ["Priority", "Supplier", "Status", "Outstanding", "Overdue Days", "Last Delivery", "Priority Score"]
    header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                             "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                          for h in headers])
    rows = []
    for rank, (_, row) in enumerate(unique_suppliers.iterrows(), 1):
        score = row["priority_score"]
        score_color = "#ef4444" if score > 0.6 else "#f97316" if score > 0.4 else "#22c55e"
        rows.append(html.Tr([
            html.Td(f"#{rank}", style={"color": "#666", "padding": "8px 10px", "fontSize": "12px", "fontWeight": "600"}),
            html.Td(row["supplier_name"], style={"color": "#fff", "padding": "8px 10px", "fontSize": "13px", "fontWeight": "500"}),
            html.Td(status_badge(row["supplier_status"]), style={"padding": "8px 10px"}),
            html.Td(f"${row['outstanding_usd']:,.0f}", style={"color": "#00c853", "padding": "8px 10px", "fontWeight": "600"}),
            html.Td(f"{int(row['overdue_days'])}d",
                    style={"color": "#ef4444" if row["overdue_days"] > 30 else "#eab308" if row["overdue_days"] > 0 else "#22c55e",
                           "padding": "8px 10px"}),
            html.Td(row["last_delivery_date"], style={"color": "#888", "padding": "8px 10px", "fontSize": "11px"}),
            html.Td([
                html.Div(f"{score:.2f}", style={"color": score_color, "fontWeight": "700", "fontSize": "13px"}),
                html.Div(style={"width": f"{score * 100:.0f}%", "height": "4px", "background": score_color,
                                "borderRadius": "2px", "marginTop": "3px", "maxWidth": "80px"})
            ], style={"padding": "8px 10px"}),
        ], style={"borderBottom": "1px solid #1a1a1a",
                  "background": "#1a0a0a" if row["supplier_status"] == "STOPPED" else "transparent"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width": "100%", "borderCollapse": "collapse"})

    # Recommendations
    recs = []
    stopped = df[df["supplier_status"] == "STOPPED"].drop_duplicates("supplier_name")
    for _, row in stopped.head(3).iterrows():
        recs.append(html.Div([
            html.Span("🔴 CRITICAL: ", style={"color": "#ef4444", "fontWeight": "700"}),
            html.Span(f"Pay {row['supplier_name']} ${row['outstanding_usd']:,.0f} immediately. Overdue {int(row['overdue_days'])} days.",
                      style={"color": "#ddd"}),
        ], style={"padding": "10px 14px", "background": "#1a0808", "border": "1px solid #ef444430",
                  "borderRadius": "8px", "marginBottom": "8px", "fontSize": "13px"}))

    limited = df[df["supplier_status"] == "LIMITED_CREDIT"].drop_duplicates("supplier_name")
    for _, row in limited.head(2).iterrows():
        recs.append(html.Div([
            html.Span("⚠️  WARNING: ", style={"color": "#f97316", "fontWeight": "700"}),
            html.Span(f"{row['supplier_name']} on limited credit — ${row['outstanding_usd']:,.0f} outstanding. Pay within 7 days.",
                      style={"color": "#ddd"}),
        ], style={"padding": "10px 14px", "background": "#1a1000", "border": "1px solid #f9731630",
                  "borderRadius": "8px", "marginBottom": "8px", "fontSize": "13px"}))

    return html.Div([
        page_header("Supplier Credit & Risk", "Accounts payable cross-referenced with stock urgency — who to pay first", "fa-file-invoice-dollar"),
        html.Div([
            confidence_block,
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_status, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_aging, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_out, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),
            html.Div([
                html.Div([
                    html.Span("💳 Smart Payment Priority Queue", style={"color": "#fff", "fontWeight": "600", "fontSize": "14px"}),
                    html.Span(" — ranked by stock urgency × overdue risk", style={"color": "#666", "fontSize": "12px"})
                ], style={"marginBottom": "16px"}),
                table
            ], style={"background": "#161616", "border": "1px solid #00c85320",
                      "borderLeft": "3px solid #00c853", "borderRadius": "10px", "padding": "20px", "marginBottom": "14px"}),
            html.Div([
                html.Div("💡 AI Recommendations", style={"color": "#888", "fontSize": "11px",
                                                          "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "14px"}),
                *recs
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
        ], style={"padding": "20px 28px"})
    ])
