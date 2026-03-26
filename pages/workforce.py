"""Workforce Intelligence — Page 14"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/workforce", name="Workforce", order=13)

def layout():
    staff = get_staff()
    revenue = get_store_revenue_summary(30)
    df = staff.merge(revenue[["store_id", "total_revenue", "total_profit"]], on="store_id", how="left")
    df["labour_pct_revenue"] = (df["monthly_labour_cost_usd"] / df["total_revenue"].replace(0, 1) * 100).round(1)
    df["revenue_per_head"] = (df["total_revenue"] / df["headcount"].replace(0, 1)).round(0)

    total_headcount = int(staff["headcount"].sum())
    total_labour = staff["monthly_labour_cost_usd"].sum()
    total_vacancies = int(staff["vacancies"].sum())
    avg_labour_pct = df["labour_pct_revenue"].mean()

    kpis = [
        kpi_card("Total Staff", str(total_headcount), None, None, "fa-users", "#3b82f6"),
        kpi_card("Monthly Labour Cost", f"${total_labour:,.0f}", None, None, "fa-money-bill", "#00c853"),
        kpi_card("Labour % of Revenue", f"{avg_labour_pct:.1f}%", None, None, "fa-percent",
                 "#22c55e" if avg_labour_pct < 15 else "#f97316"),
        kpi_card("Open Vacancies", str(total_vacancies), None, None, "fa-user-plus", "#eab308"),
    ]

    # Revenue vs Labour
    fig_lr = go.Figure()
    fig_lr.add_trace(go.Bar(x=df["store_name"], y=df["total_revenue"],
                             name="Monthly Revenue", marker_color="#3b82f6", opacity=0.8))
    fig_lr.add_trace(go.Bar(x=df["store_name"], y=df["monthly_labour_cost_usd"],
                             name="Labour Cost", marker_color="#00c853", opacity=0.9))
    fig_lr.update_layout(**CHART_LAYOUT, barmode="group",
                          title={"text": "Revenue vs Labour Cost by Store", "font": {"color": "#ccc", "size": 13}})
    fig_lr.update_xaxes(tickangle=-30)

    # Headcount
    df_sorted = df.sort_values("headcount", ascending=True)
    fig_hc = go.Figure(go.Bar(
        x=df_sorted["headcount"], y=df_sorted["store_name"],
        orientation="h", marker_color="#8b5cf6",
        text=df_sorted["headcount"], textposition="outside"
    ))
    fig_hc.update_layout(**CHART_LAYOUT,
                          title={"text": "Staff Headcount by Store", "font": {"color": "#ccc", "size": 13}})

    # Overtime
    df_ot = df.sort_values("overtime_hours_this_month", ascending=False)
    ot_colors = ["#ef4444" if h > 60 else "#f97316" if h > 30 else "#22c55e"
                 for h in df_ot["overtime_hours_this_month"]]
    fig_ot = go.Figure(go.Bar(
        x=df_ot["store_name"], y=df_ot["overtime_hours_this_month"],
        marker_color=ot_colors,
        text=df_ot["overtime_hours_this_month"].apply(lambda x: f"{x}h"), textposition="outside"
    ))
    fig_ot.add_hline(y=40, line_dash="dash", line_color="#666", annotation_text="40h alert")
    fig_ot.update_layout(**CHART_LAYOUT,
                          title={"text": "Overtime Hours This Month", "font": {"color": "#ccc", "size": 13}})
    fig_ot.update_xaxes(tickangle=-30)

    # Tenure
    fig_tenure = go.Figure(go.Bar(
        x=df["store_name"], y=df["avg_tenure_years"],
        marker_color=["#22c55e" if t > 4 else "#eab308" if t > 2 else "#ef4444"
                      for t in df["avg_tenure_years"]],
        text=df["avg_tenure_years"].apply(lambda x: f"{x:.1f}y"), textposition="outside"
    ))
    fig_tenure.update_layout(**CHART_LAYOUT,
                              title={"text": "Avg Staff Tenure by Store (years)", "font": {"color": "#ccc", "size": 13}})
    fig_tenure.update_xaxes(tickangle=-30)

    # Summary table
    headers = ["Store", "Staff", "Labour $", "Labour %", "Rev/Head", "Vacancies"]
    header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "7px 8px",
                                             "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                          for h in headers])
    rows = []
    for _, row in df.sort_values("labour_pct_revenue", ascending=False).iterrows():
        lp = row["labour_pct_revenue"]
        lp_color = "#22c55e" if lp < 12 else "#f97316" if lp < 18 else "#ef4444"
        rows.append(html.Tr([
            html.Td(row["store_name"][:16], style={"color": "#ddd", "padding": "6px 8px", "fontSize": "11px"}),
            html.Td(str(int(row["headcount"])), style={"color": "#aaa", "padding": "6px 8px"}),
            html.Td(f"${row['monthly_labour_cost_usd']:,.0f}", style={"color": "#00c853", "padding": "6px 8px"}),
            html.Td(f"{lp:.1f}%", style={"color": lp_color, "padding": "6px 8px", "fontWeight": "600"}),
            html.Td(f"${row['revenue_per_head']:,.0f}", style={"color": "#3b82f6", "padding": "6px 8px"}),
            html.Td(str(int(row["vacancies"])),
                    style={"color": "#eab308" if row["vacancies"] > 0 else "#444", "padding": "6px 8px"}),
        ], style={"borderBottom": "1px solid #1a1a1a"}))

    table = html.Div([
        html.Div("Store Labour Summary", style={"color": "#888", "fontSize": "11px",
                                                  "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "12px"}),
        html.Table([html.Thead(header_row), html.Tbody(rows)],
                   style={"width": "100%", "borderCollapse": "collapse"})
    ])

    return html.Div([
        page_header("Workforce Intelligence",
                    "Staff headcount, labour costs vs revenue, overtime and vacancies", "fa-users"),
        html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_lr, config={"displayModeBar": False}, style={"height": "300px"})],
                         style={"flex": "1.5", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_hc, config={"displayModeBar": False}, style={"height": "300px"})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_ot, config={"displayModeBar": False}, style={"height": "260px"})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_tenure, config={"displayModeBar": False}, style={"height": "260px"})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div(table, style={"flex": "1", "background": "#161616", "border": "1px solid #222",
                                        "borderRadius": "10px", "padding": "20px"}),
            ], style={"display": "flex", "gap": "14px"}),
        ], style={"padding": "20px 28px"})
    ])
