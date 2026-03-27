"""Shrinkage & Loss — Page 15"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/shrinkage", name="Shrinkage & Loss", order=14)

def layout():
    try:
        df = get_shrinkage()

        # Ensure store_name is a flat string column (join may produce multi-index)
        df = df.reset_index(drop=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns]

        # Flatten any list/array values in store_name
        if "store_name" in df.columns:
            df["store_name"] = df["store_name"].astype(str)
        else:
            # fallback — use store_id if store_name missing
            df["store_name"] = df.get("store_id", "Unknown").astype(str)

        total_loss = float(df["value_usd"].sum())
        monthly_totals = df.groupby("month", as_index=False)["value_usd"].sum()
        avg_monthly = float(monthly_totals["value_usd"].mean()) if len(monthly_totals) > 0 else 0

        store_totals = df.groupby("store_name", as_index=False)["value_usd"].sum()
        worst_store = store_totals.loc[store_totals["value_usd"].idxmax(), "store_name"] if len(store_totals) > 0 else "N/A"
        worst_store = str(worst_store)[:15]

        theft_mask = df["cause"].str.strip() == "Theft"
        theft = float(df.loc[theft_mask, "value_usd"].sum())

        kpis = [
            kpi_card("Total Losses (6mo)", f"${total_loss:,.0f}", None, None, "fa-circle-minus", "#ef4444"),
            kpi_card("Avg Monthly Loss", f"${avg_monthly:,.0f}", None, None, "fa-calendar", "#f97316"),
            kpi_card("Theft Losses", f"${theft:,.0f}", None, None, "fa-user-secret", "#8b5cf6"),
            kpi_card("Highest Loss Store", worst_store, None, None, "fa-store", "#eab308"),
        ]

        # Loss by cause
        cause_totals = df.groupby("cause", as_index=False)["value_usd"].sum().sort_values("value_usd", ascending=False)
        fig_cause = go.Figure(go.Bar(
            x=cause_totals["cause"].astype(str),
            y=cause_totals["value_usd"],
            marker_color=["#ef4444", "#f97316", "#eab308", "#8b5cf6", "#3b82f6"][:len(cause_totals)]
        ))
        fig_cause.update_layout(**CHART_LAYOUT,
                                 title={"text": "Loss by Cause", "font": {"color": "#ccc", "size": 13}})

        # Loss by store
        store_plot = store_totals.sort_values("value_usd", ascending=True)
        n = len(store_plot)
        fig_store = go.Figure(go.Bar(
            x=store_plot["value_usd"],
            y=store_plot["store_name"].astype(str),
            orientation="h",
            marker_color=["#ef4444" if i == n-1 else "#f97316" if i >= n-3 else "#3b82f6"
                          for i in range(n)]
        ))
        fig_store.update_layout(**CHART_LAYOUT,
                                 title={"text": "Loss by Store", "font": {"color": "#ccc", "size": 13}})

        # Monthly trend by cause
        monthly_cause = df.groupby(["month", "cause"], as_index=False)["value_usd"].sum()
        fig_trend = px.bar(monthly_cause, x="month", y="value_usd", color="cause", barmode="stack")
        fig_trend.update_layout(**CHART_LAYOUT,
                                 title={"text": "Monthly Loss Trend by Cause", "font": {"color": "#ccc", "size": 13}})
        fig_trend.update_xaxes(tickangle=-30)

        return html.Div([
            page_header("Shrinkage & Loss",
                        "Theft, damage, expiry and admin errors — where inventory value disappears",
                        "fa-triangle-exclamation"),
            html.Div([
                html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                         style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
                html.Div([
                    html.Div([dcc.Graph(figure=fig_cause, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_store, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_trend, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                ], style={"display": "flex", "gap": "14px"}),
            ], style={"padding": "20px 28px"})
        ])

    except Exception as e:
        import traceback
        return html.Div([
            page_header("Shrinkage & Loss", "Error loading data", "fa-triangle-exclamation"),
            html.Div([
                html.Div(f"⚠️ Error: {str(e)}", style={"color": "#ef4444", "padding": "20px"}),
                html.Pre(traceback.format_exc(), style={"color": "#888", "fontSize": "11px", "padding": "20px"})
            ])
        ])
