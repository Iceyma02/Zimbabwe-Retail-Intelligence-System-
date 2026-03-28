"""Promotions ROI Tracker — Page 11 with Retailer Filter"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/promotions", name="Promotions ROI", order=10)

def layout():
    return html.Div([
        page_header("Promotions ROI Tracker",
                    "Did our promotions actually work? Revenue lift vs margin impact", "fa-tags"),
        html.Div(id="promotions-content", style={"padding": "20px 28px"})
    ])


@callback(
    Output("promotions-content", "children"),
    Input("active-retailer", "data")
)
def update_promotions(retailer):
    try:
        df = get_promotions()
        
        if df.empty:
            return html.Div([
                html.Div("No promotions data available", 
                        style={"textAlign": "center", "padding": "60px", "color": "#888"})
            ])
        
        retailer_name = retailer if retailer != "ALL" else "All Retailers"
        
        active = df[df["status"] == "ACTIVE"]
        avg_roi = df["roi_percent"].mean()
        best = df.loc[df["roi_percent"].idxmax()]
        total_lift = (df["promo_revenue"] - df["pre_promo_revenue"]).sum()

        kpis = [
            kpi_card("Active Promotions", str(len(active)), None, None, "fa-tag", "#00c853"),
            kpi_card("Avg ROI", f"{avg_roi:.1f}%", None, None, "fa-percent",
                     "#22c55e" if avg_roi > 0 else "#ef4444"),
            kpi_card("Total Revenue Lift", f"${total_lift:,.0f}", None, None, "fa-arrow-up", "#3b82f6"),
            kpi_card("Best Promo", best["promo_name"][:20], None, None, "fa-trophy", "#eab308"),
        ]

        fig_roi = go.Figure(go.Bar(
            x=df["promo_name"].str[:20], y=df["roi_percent"],
            marker_color=["#22c55e" if r > 0 else "#ef4444" for r in df["roi_percent"]],
            text=df["roi_percent"].apply(lambda x: f"{x:.0f}%"), textposition="outside"
        ))
        fig_roi.update_layout(**CHART_LAYOUT,
                               title={"text": f"ROI % by Promotion - {retailer_name}", "font": {"color": "#ccc", "size": 13}})
        fig_roi.update_xaxes(tickangle=-30)

        fig_lift = go.Figure()
        fig_lift.add_trace(go.Bar(x=df["promo_name"].str[:18], y=df["pre_promo_revenue"],
                                   name="Pre-Promo", marker_color="#444"))
        fig_lift.add_trace(go.Bar(x=df["promo_name"].str[:18], y=df["promo_revenue"],
                                   name="During Promo", marker_color="#00c853", opacity=0.8))
        fig_lift.update_layout(**CHART_LAYOUT, barmode="overlay",
                                title={"text": f"Revenue Lift by Promotion - {retailer_name}", "font": {"color": "#ccc", "size": 13}})
        fig_lift.update_xaxes(tickangle=-30)

        headers = ["Promotion", "Period", "Pre Revenue", "Promo Revenue", "Cost", "ROI", "Status"]
        header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                                 "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                              for h in headers])
        rows = []
        for _, row in df.sort_values("roi_percent", ascending=False).iterrows():
            roi_color = "#22c55e" if row["roi_percent"] > 0 else "#ef4444"
            rows.append(html.Tr([
                html.Td(row["promo_name"], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
                html.Td(f"{row['start_date']} → {row['end_date']}", style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
                html.Td(f"${row['pre_promo_revenue']:,.0f}", style={"color": "#888", "padding": "7px 10px"}),
                html.Td(f"${row['promo_revenue']:,.0f}", style={"color": "#fff", "padding": "7px 10px", "fontWeight": "600"}),
                html.Td(f"${row['promo_cost_usd']:,.0f}", style={"color": "#f97316", "padding": "7px 10px"}),
                html.Td(f"{row['roi_percent']:.1f}%", style={"color": roi_color, "padding": "7px 10px", "fontWeight": "700"}),
                html.Td(status_badge(row["status"]), style={"padding": "7px 10px"}),
            ], style={"borderBottom": "1px solid #1a1a1a"}))
        table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                           style={"width": "100%", "borderCollapse": "collapse"})

        return html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_roi, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_lift, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),
            html.Div([
                html.Div("Promotion Performance Table", style={"color": "#888", "fontSize": "11px",
                                                                "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "14px"}),
                table
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px", "overflowX": "auto"}),
        ])
        
    except Exception as e:
        print(f"Error in promotions: {e}")
        return html.Div([
            html.Div("⚠️ Error Loading Data", style={
                "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
            }),
            html.Div(str(e), style={"color": "#888", "fontSize": "14px"})
        ], style={"textAlign": "center", "padding": "60px"})
