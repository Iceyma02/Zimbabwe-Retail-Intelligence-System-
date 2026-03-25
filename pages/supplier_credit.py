"""Supplier Credit & Risk — Page 10 (The Crown Jewel)"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/supplier-credit", name="Supplier Credit", order=9)

def compute_priority_score(row, inv_df):
    """Priority Score = Stock Urgency×0.4 + Overdue Days×0.3 + Supplier Status×0.2 + Replaceability×0.1"""
    status_score = {"STOPPED": 1.0, "LIMITED_CREDIT": 0.6, "ACTIVE": 0.1}.get(row["supplier_status"], 0.2)
    overdue_score = min(row["overdue_days"] / 60, 1.0)

    # Stock urgency — find products tied to this supplier
    stock_urgency = 0.3
    outstanding_pct = row["outstanding_usd"] / max(row["amount_usd"], 1)

    score = (stock_urgency * 0.4 + overdue_score * 0.3 + status_score * 0.2 + outstanding_pct * 0.1)
    return round(score, 3)

def layout():
    return html.Div([
        page_header("Supplier Credit & Risk", "Accounts payable cross-referenced with stock urgency — who to pay first", "fa-file-invoice-dollar"),
        html.Div([
            # Confidence Index
            html.Div(id="sci-confidence-block", style={"marginBottom":"20px"}),

            # KPIs
            html.Div(id="sci-kpis", style={"display":"flex","gap":"14px","marginBottom":"20px"}),

            html.Div([
                # Supplier health summary
                html.Div([
                    dcc.Graph(id="sci-status-chart", config={"displayModeBar":False}, style={"height":"280px"})
                ], style={"flex":1,"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"16px"}),
                # Overdue age
                html.Div([
                    dcc.Graph(id="sci-overdue-chart", config={"displayModeBar":False}, style={"height":"280px"})
                ], style={"flex":1,"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"16px"}),
                # Outstanding by supplier
                html.Div([
                    dcc.Graph(id="sci-outstanding-chart", config={"displayModeBar":False}, style={"height":"280px"})
                ], style={"flex":1,"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"16px"}),
            ], style={"display":"flex","gap":"14px","marginBottom":"14px"}),

            # Priority payment table
            html.Div([
                html.Div([
                    html.Span("💳 Smart Payment Priority Queue", style={"color":"#fff","fontWeight":"600","fontSize":"14px"}),
                    html.Span(" — ranked by stock urgency × overdue risk",
                              style={"color":"#666","fontSize":"12px"})
                ], style={"marginBottom":"16px"}),
                html.Div(id="sci-priority-table")
            ], style={"background":"#161616","border":"1px solid #e3183720","borderLeft":"3px solid #e31837",
                      "borderRadius":"10px","padding":"20px"}),

            # Recommendations
            html.Div(id="sci-recommendations", style={"marginTop":"14px"})

        ], style={"padding":"20px 28px"}),
        dcc.Interval(id="sci-load", interval=99999999, n_intervals=0, max_intervals=1)
    ])


@callback(
    Output("sci-confidence-block","children"),
    Output("sci-kpis","children"),
    Output("sci-status-chart","figure"),
    Output("sci-overdue-chart","figure"),
    Output("sci-outstanding-chart","figure"),
    Output("sci-priority-table","children"),
    Output("sci-recommendations","children"),
    Input("sci-load","n_intervals")
)
def update_credit(_):
    df = get_supplier_credit()
    inv = get_inventory_simple()

    # Compute priority scores
    df["priority_score"] = df.apply(lambda r: compute_priority_score(r, inv), axis=1)
    df = df.sort_values("priority_score", ascending=False)

    # Confidence Index (0–100)
    active_count = len(df[df["supplier_status"]=="ACTIVE"]["supplier_name"].unique())
    limited_count = len(df[df["supplier_status"]=="LIMITED_CREDIT"]["supplier_name"].unique())
    stopped_count = len(df[df["supplier_status"]=="STOPPED"]["supplier_name"].unique())
    total_suppliers = active_count + limited_count + stopped_count
    confidence = int(((active_count * 1.0 + limited_count * 0.4) / max(total_suppliers, 1)) * 100)
    conf_color = "#22c55e" if confidence > 70 else "#eab308" if confidence > 45 else "#ef4444"

    confidence_block = html.Div([
        html.Div([
            html.Div([
                html.Div("SUPPLIER CONFIDENCE INDEX", style={"color":"#888","fontSize":"11px","letterSpacing":"1px"}),
                html.Div([
                    html.Span(f"{confidence}", style={"fontSize":"52px","fontWeight":"800",
                                                        "color":conf_color,"fontFamily":"'Syne',sans-serif"}),
                    html.Span("/100", style={"color":"#444","fontSize":"24px","marginLeft":"4px"}),
                    html.Span(" ⚠️" if confidence < 70 else " ✅",
                              style={"fontSize":"20px","marginLeft":"8px"})
                ]),
            ]),
            html.Div([
                html.Div([
                    html.Div(f"✅ Actively trading: {active_count} suppliers",
                             style={"color":"#22c55e","fontSize":"13px","margin":"4px 0"}),
                    html.Div(f"⚠️  Limited credit: {limited_count} suppliers",
                             style={"color":"#eab308","fontSize":"13px","margin":"4px 0"}),
                    html.Div(f"❌ Stopped trading: {stopped_count} suppliers",
                             style={"color":"#ef4444","fontSize":"13px","margin":"4px 0"}),
                ], style={"background":"#1a1a1a","border":"1px solid #2a2a2a","borderRadius":"8px","padding":"12px 16px"})
            ])
        ], style={"display":"flex","alignItems":"center","justifyContent":"space-between","gap":"40px"})
    ], style={"background":"#161616","border":f"1px solid {conf_color}30",
              "borderLeft":f"4px solid {conf_color}","borderRadius":"10px","padding":"20px"})

    # KPIs
    total_outstanding = df["outstanding_usd"].sum()
    total_overdue = df[df["overdue_days"] > 0]["outstanding_usd"].sum()
    critical_suppliers = len(df[(df["supplier_status"]=="STOPPED") | (df["overdue_days"]>30)]["supplier_name"].unique())

    kpis = [
        kpi_card("Total Outstanding", f"${total_outstanding:,.0f}", None, None, "fa-dollar-sign", "#00c853"),
        kpi_card("Overdue Amount", f"${total_overdue:,.0f}", None, None, "fa-clock", "#f97316"),
        kpi_card("At-Risk Suppliers", str(critical_suppliers), None, None, "fa-triangle-exclamation", "#ef4444"),
        kpi_card("Active Suppliers", str(active_count), None, None, "fa-handshake", "#22c55e"),
    ]

    # Status chart
    sup_status = df.groupby(["supplier_name","supplier_status"])["outstanding_usd"].sum().reset_index()
    sup_status = sup_status.sort_values("outstanding_usd", ascending=False).head(14)
    status_color_map = {"ACTIVE":"#22c55e","LIMITED_CREDIT":"#f97316","STOPPED":"#ef4444"}
    fig_status = go.Figure()
    for status, color in status_color_map.items():
        sub = sup_status[sup_status["supplier_status"]==status]
        if not sub.empty:
            fig_status.add_trace(go.Bar(
                x=sub["outstanding_usd"], y=sub["supplier_name"],
                name=status.replace("_"," "), orientation="h",
                marker_color=color
            ))
    fig_status.update_layout(**CHART_LAYOUT, barmode="stack",
                              title={"text":"Outstanding by Supplier & Status","font":{"color":"#ccc","size":13}},
                              yaxis={"categoryorder":"total ascending"})

    # Overdue aging buckets
    bins = pd.cut(df["overdue_days"], bins=[-1,0,14,30,60,999],
                  labels=["Current","1-14d","15-30d","31-60d","60d+"])
    age_amounts = df.groupby(bins)["outstanding_usd"].sum().reset_index()
    age_amounts.columns = ["bucket","amount"]
    fig_aging = go.Figure(go.Bar(
        x=age_amounts["bucket"].astype(str), y=age_amounts["amount"],
        marker_color=["#22c55e","#3b82f6","#eab308","#f97316","#ef4444"]
    ))
    fig_aging.update_layout(**CHART_LAYOUT, title={"text":"Accounts Payable Aging","font":{"color":"#ccc","size":13}})

    # Outstanding by supplier (top 10)
    top_outstanding = df.groupby("supplier_name")["outstanding_usd"].sum().sort_values(ascending=False).head(10)
    fig_outstanding = go.Figure(go.Bar(
        x=top_outstanding.values, y=top_outstanding.index,
        orientation="h",
        marker_color="#00c853"
    ))
    fig_outstanding.update_layout(**CHART_LAYOUT, title={"text":"Top 10 Outstanding Balances","font":{"color":"#ccc","size":13}},
                                   yaxis={"categoryorder":"total ascending"})

    # Priority table
    unique_suppliers = df.drop_duplicates("supplier_name").head(15)
    headers = ["Priority","Supplier","Status","Outstanding","Overdue Days","Last Delivery","Priority Score"]
    header_row = html.Tr([html.Th(h, style={"color":"#666","fontSize":"11px","padding":"8px 10px",
                                             "borderBottom":"1px solid #2a2a2a","textTransform":"uppercase"}) for h in headers])
    rows = []
    for rank, (_, row) in enumerate(unique_suppliers.iterrows(), 1):
        score = row["priority_score"]
        score_color = "#ef4444" if score > 0.6 else "#f97316" if score > 0.4 else "#22c55e"
        rows.append(html.Tr([
            html.Td(f"#{rank}", style={"color":"#666","padding":"8px 10px","fontSize":"12px","fontWeight":"600"}),
            html.Td(row["supplier_name"], style={"color":"#fff","padding":"8px 10px","fontSize":"13px","fontWeight":"500"}),
            html.Td(status_badge(row["supplier_status"]), style={"padding":"8px 10px"}),
            html.Td(f"${row['outstanding_usd']:,.0f}", style={"color":"#00c853","padding":"8px 10px","fontWeight":"600"}),
            html.Td(f"{int(row['overdue_days'])}d",
                    style={"color":"#ef4444" if row["overdue_days"] > 30 else "#eab308" if row["overdue_days"] > 0 else "#22c55e",
                           "padding":"8px 10px"}),
            html.Td(row["last_delivery_date"], style={"color":"#888","padding":"8px 10px","fontSize":"11px"}),
            html.Td([
                html.Div(f"{score:.2f}", style={"color":score_color,"fontWeight":"700","fontSize":"13px"}),
                html.Div(style={"width":f"{score*100:.0f}%","height":"4px","background":score_color,
                                "borderRadius":"2px","marginTop":"3px","maxWidth":"80px"})
            ], style={"padding":"8px 10px"}),
        ], style={"borderBottom":"1px solid #1a1a1a",
                  "background":"#1a0a0a" if row["supplier_status"]=="STOPPED" else "transparent"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width":"100%","borderCollapse":"collapse"})

    # Recommendations
    recs = []
    stopped = df[df["supplier_status"]=="STOPPED"].drop_duplicates("supplier_name")
    for _, row in stopped.head(3).iterrows():
        recs.append(html.Div([
            html.Span("🔴 CRITICAL: ", style={"color":"#ef4444","fontWeight":"700"}),
            html.Span(f"Pay {row['supplier_name']} ${row['outstanding_usd']:,.0f} immediately to restart supply. ",
                      style={"color":"#ddd"}),
            html.Span(f"Overdue {int(row['overdue_days'])} days.", style={"color":"#888"}),
        ], style={"padding":"10px 14px","background":"#1a0808","border":"1px solid #ef444430",
                  "borderRadius":"8px","marginBottom":"8px","fontSize":"13px"}))

    limited = df[df["supplier_status"]=="LIMITED_CREDIT"].drop_duplicates("supplier_name")
    for _, row in limited.head(2).iterrows():
        recs.append(html.Div([
            html.Span("⚠️  WARNING: ", style={"color":"#f97316","fontWeight":"700"}),
            html.Span(f"{row['supplier_name']} on limited credit — outstanding ${row['outstanding_usd']:,.0f}. Pay within 7 days.",
                      style={"color":"#ddd"}),
        ], style={"padding":"10px 14px","background":"#1a1000","border":"1px solid #f9731630",
                  "borderRadius":"8px","marginBottom":"8px","fontSize":"13px"}))

    recs_block = html.Div([
        html.Div("💡 AI Recommendations", style={"color":"#888","fontSize":"11px","textTransform":"uppercase",
                                                   "letterSpacing":"1px","marginBottom":"14px"}),
        *recs
    ], style={"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"20px"})

    return confidence_block, [html.Div(k, style={"flex":1}) for k in kpis], fig_status, fig_aging, fig_outstanding, table, recs_block
