"""Supplier Credit & Risk — Page 10"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/supplier-credit", name="Supplier Credit", order=9)

def compute_priority_score(row):
    status_score = {"STOPPED": 1.0, "LIMITED_CREDIT": 0.6, "ACTIVE": 0.1}.get(
        str(row["supplier_status"]), 0.2)
    overdue_score = min(float(row["overdue_days"]) / 60.0, 1.0)
    outstanding_pct = float(row["outstanding_usd"]) / max(float(row["amount_usd"]), 1.0)
    return round((0.3 * 0.4 + overdue_score * 0.3 + status_score * 0.2 + outstanding_pct * 0.1), 3)

def layout():
    try:
        df = get_supplier_credit()
        df = df.reset_index(drop=True)

        df["priority_score"] = df.apply(compute_priority_score, axis=1)
        df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

        active_count = int(df[df["supplier_status"] == "ACTIVE"]["supplier_name"].nunique())
        limited_count = int(df[df["supplier_status"] == "LIMITED_CREDIT"]["supplier_name"].nunique())
        stopped_count = int(df[df["supplier_status"] == "STOPPED"]["supplier_name"].nunique())
        total_suppliers = active_count + limited_count + stopped_count
        confidence = int(((active_count * 1.0 + limited_count * 0.4) / max(total_suppliers, 1)) * 100)
        conf_color = "#22c55e" if confidence > 70 else "#eab308" if confidence > 45 else "#ef4444"

        confidence_block = html.Div([
            html.Div([
                html.Div([
                    html.Div("SUPPLIER CONFIDENCE INDEX",
                             style={"color": "#888", "fontSize": "11px", "letterSpacing": "1px"}),
                    html.Div([
                        html.Span(f"{confidence}", style={"fontSize": "52px", "fontWeight": "800",
                                                           "color": conf_color, "fontFamily": "'Syne',sans-serif"}),
                        html.Span("/100", style={"color": "#444", "fontSize": "24px", "marginLeft": "4px"}),
                        html.Span(" ⚠️" if confidence < 70 else " ✅",
                                  style={"fontSize": "20px", "marginLeft": "8px"})
                    ]),
                ]),
                html.Div([
                    html.Div(f"✅ Actively trading: {active_count} suppliers",
                             style={"color": "#22c55e", "fontSize": "13px", "margin": "4px 0"}),
                    html.Div(f"⚠️  Limited credit: {limited_count} suppliers",
                             style={"color": "#eab308", "fontSize": "13px", "margin": "4px 0"}),
                    html.Div(f"❌ Stopped trading: {stopped_count} suppliers",
                             style={"color": "#ef4444", "fontSize": "13px", "margin": "4px 0"}),
                ], style={"background": "#1a1a1a", "border": "1px solid #2a2a2a",
                           "borderRadius": "8px", "padding": "12px 16px"})
            ], style={"display": "flex", "alignItems": "center",
                      "justifyContent": "space-between", "gap": "40px"})
        ], style={"background": "#161616", "border": f"1px solid {conf_color}30",
                  "borderLeft": f"4px solid {conf_color}", "borderRadius": "10px",
                  "padding": "20px", "marginBottom": "20px"})

        total_outstanding = float(df["outstanding_usd"].sum())
        total_overdue = float(df[df["overdue_days"] > 0]["outstanding_usd"].sum())
        critical_suppliers = int(df[
            (df["supplier_status"] == "STOPPED") | (df["overdue_days"] > 30)
        ]["supplier_name"].nunique())

        kpis = [
            kpi_card("Total Outstanding", f"${total_outstanding:,.0f}", None, None, "fa-dollar-sign", "#00c853"),
            kpi_card("Overdue Amount", f"${total_overdue:,.0f}", None, None, "fa-clock", "#f97316"),
            kpi_card("At-Risk Suppliers", str(critical_suppliers), None, None, "fa-triangle-exclamation", "#ef4444"),
            kpi_card("Active Suppliers", str(active_count), None, None, "fa-handshake", "#22c55e"),
        ]

        # Status chart
        sup_status = df.groupby(
            ["supplier_name", "supplier_status"], as_index=False, observed=True
        )["outstanding_usd"].sum()
        sup_status = sup_status.sort_values("outstanding_usd", ascending=False).head(14)
        status_color_map = {"ACTIVE": "#22c55e", "LIMITED_CREDIT": "#f97316", "STOPPED": "#ef4444"}
        fig_status = go.Figure()
        for status, color in status_color_map.items():
            sub = sup_status[sup_status["supplier_status"] == status]
            if not sub.empty:
                fig_status.add_trace(go.Bar(
                    x=sub["outstanding_usd"].tolist(),
                    y=sub["supplier_name"].tolist(),
                    name=status.replace("_", " "), orientation="h", marker_color=color
                ))
        fig_status.update_layout(**CHART_LAYOUT, barmode="stack",
                                  title={"text": "Outstanding by Supplier & Status",
                                         "font": {"color": "#ccc", "size": 13}},
                                  yaxis={"categoryorder": "total ascending"})

        # Aging buckets
        bins = pd.cut(df["overdue_days"].astype(float),
                      bins=[-1, 0, 14, 30, 60, 9999],
                      labels=["Current", "1-14d", "15-30d", "31-60d", "60d+"])
        age_df = df.groupby(bins, observed=True)["outstanding_usd"].sum().reset_index()
        age_df.columns = ["bucket", "amount"]
        fig_aging = go.Figure(go.Bar(
            x=age_df["bucket"].astype(str).tolist(),
            y=age_df["amount"].tolist(),
            marker_color=["#22c55e", "#3b82f6", "#eab308", "#f97316", "#ef4444"]
        ))
        fig_aging.update_layout(**CHART_LAYOUT,
                                 title={"text": "Accounts Payable Aging", "font": {"color": "#ccc", "size": 13}})

        # Top outstanding
        top_out = df.groupby("supplier_name", as_index=False)["outstanding_usd"].sum()
        top_out = top_out.sort_values("outstanding_usd", ascending=False).head(10)
        fig_out = go.Figure(go.Bar(
            x=top_out["outstanding_usd"].tolist(),
            y=top_out["supplier_name"].tolist(),
            orientation="h", marker_color="#00c853"
        ))
        fig_out.update_layout(**CHART_LAYOUT,
                               title={"text": "Top 10 Outstanding Balances", "font": {"color": "#ccc", "size": 13}},
                               yaxis={"categoryorder": "total ascending"})

        # Priority table
        unique_suppliers = df.drop_duplicates("supplier_name").head(15).reset_index(drop=True)
        headers = ["Priority", "Supplier", "Status", "Outstanding", "Overdue Days", "Last Delivery", "Score"]
        header_row = html.Tr([
            html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                               "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
            for h in headers
        ])
        rows = []
        for rank, (_, row) in enumerate(unique_suppliers.iterrows(), 1):
            score = float(row["priority_score"])
            score_color = "#ef4444" if score > 0.6 else "#f97316" if score > 0.4 else "#22c55e"
            overdue = float(row["overdue_days"])
            rows.append(html.Tr([
                html.Td(f"#{rank}", style={"color": "#666", "padding": "8px 10px", "fontSize": "12px", "fontWeight": "600"}),
                html.Td(str(row["supplier_name"]), style={"color": "#fff", "padding": "8px 10px", "fontSize": "13px", "fontWeight": "500"}),
                html.Td(status_badge(str(row["supplier_status"])), style={"padding": "8px 10px"}),
                html.Td(f"${float(row['outstanding_usd']):,.0f}", style={"color": "#00c853", "padding": "8px 10px", "fontWeight": "600"}),
                html.Td(f"{int(overdue)}d", style={
                    "color": "#ef4444" if overdue > 30 else "#eab308" if overdue > 0 else "#22c55e",
                    "padding": "8px 10px"
                }),
                html.Td(str(row["last_delivery_date"]), style={"color": "#888", "padding": "8px 10px", "fontSize": "11px"}),
                html.Td([
                    html.Div(f"{score:.2f}", style={"color": score_color, "fontWeight": "700", "fontSize": "13px"}),
                    html.Div(style={"width": f"{min(score * 100, 100):.0f}%", "height": "4px",
                                    "background": score_color, "borderRadius": "2px",
                                    "marginTop": "3px", "maxWidth": "80px"})
                ], style={"padding": "8px 10px"}),
            ], style={"borderBottom": "1px solid #1a1a1a",
                      "background": "#1a0a0a" if str(row["supplier_status"]) == "STOPPED" else "transparent"}))

        table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                           style={"width": "100%", "borderCollapse": "collapse"})

        # Recommendations
        recs = []
        stopped_df = df[df["supplier_status"] == "STOPPED"].drop_duplicates("supplier_name")
        for _, row in stopped_df.head(3).iterrows():
            recs.append(html.Div([
                html.Span("🔴 CRITICAL: ", style={"color": "#ef4444", "fontWeight": "700"}),
                html.Span(f"Pay {row['supplier_name']} ${float(row['outstanding_usd']):,.0f} immediately. "
                          f"Overdue {int(row['overdue_days'])} days.", style={"color": "#ddd"}),
            ], style={"padding": "10px 14px", "background": "#1a0808",
                      "border": "1px solid #ef444430", "borderRadius": "8px", "marginBottom": "8px", "fontSize": "13px"}))

        limited_df = df[df["supplier_status"] == "LIMITED_CREDIT"].drop_duplicates("supplier_name")
        for _, row in limited_df.head(2).iterrows():
            recs.append(html.Div([
                html.Span("⚠️  WARNING: ", style={"color": "#f97316", "fontWeight": "700"}),
                html.Span(f"{row['supplier_name']} on limited credit — "
                          f"${float(row['outstanding_usd']):,.0f} outstanding. Pay within 7 days.", style={"color": "#ddd"}),
            ], style={"padding": "10px 14px", "background": "#1a1000",
                      "border": "1px solid #f9731630", "borderRadius": "8px", "marginBottom": "8px", "fontSize": "13px"}))

        if not recs:
            recs = [html.Div("✅ All suppliers are in good standing.", style={"color": "#22c55e", "fontSize": "13px"})]

        return html.Div([
            page_header("Supplier Credit & Risk",
                        "Accounts payable cross-referenced with stock urgency — who to pay first",
                        "fa-file-invoice-dollar"),
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
                        html.Span("💳 Smart Payment Priority Queue",
                                  style={"color": "#fff", "fontWeight": "600", "fontSize": "14px"}),
                        html.Span(" — ranked by stock urgency × overdue risk",
                                  style={"color": "#666", "fontSize": "12px"})
                    ], style={"marginBottom": "16px"}),
                    table
                ], style={"background": "#161616", "border": "1px solid #00c85320",
                           "borderLeft": "3px solid #00c853", "borderRadius": "10px",
                           "padding": "20px", "marginBottom": "14px"}),
                html.Div([
                    html.Div("💡 AI Recommendations", style={"color": "#888", "fontSize": "11px",
                                                              "textTransform": "uppercase", "letterSpacing": "1px",
                                                              "marginBottom": "14px"}),
                    *recs
                ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px"}),
            ], style={"padding": "20px 28px"})
        ])

    except Exception as e:
        import traceback
        return html.Div([
            page_header("Supplier Credit & Risk", "Error loading data", "fa-file-invoice-dollar"),
            html.Div([
                html.Div(f"⚠️ Error: {str(e)}", style={"color": "#ef4444", "padding": "20px"}),
                html.Pre(traceback.format_exc(), style={"color": "#888", "fontSize": "11px", "padding": "20px"})
            ])
        ])
