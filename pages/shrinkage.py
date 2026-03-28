"""Shrinkage & Loss — Page 15"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/shrinkage", name="Shrinkage & Loss", order=14)

def flatten_value(val):
    """Flatten any nested value to a simple string"""
    if val is None:
        return "Unknown"
    if isinstance(val, (list, tuple, np.ndarray)):
        if len(val) > 0:
            return str(val[0])
        return "Unknown"
    if hasattr(val, 'iloc'):
        try:
            return str(val.iloc[0])
        except:
            return str(val)
    return str(val)

def layout():
    try:
        df = get_shrinkage()
        
        if df.empty:
            return html.Div([
                page_header("Shrinkage & Loss",
                            "Theft, damage, expiry and admin errors — where inventory value disappears",
                            "fa-triangle-exclamation"),
                html.Div([
                    html.Div("No shrinkage data available", 
                            style={"textAlign": "center", "padding": "60px", "color": "#888"})
                ], style={"padding": "20px 28px"})
            ])
        
        # Make a copy
        df_shrink = df.copy()
        
        # Flatten all columns to simple strings
        for col in df_shrink.columns:
            if col != "value_usd":
                df_shrink[col] = df_shrink[col].apply(flatten_value)
        
        # Ensure value_usd is numeric
        df_shrink["value_usd"] = pd.to_numeric(df_shrink["value_usd"], errors='coerce').fillna(0)
        
        # Create a clean DataFrame by extracting individual columns
        df_clean = pd.DataFrame()
        
        # Extract store_name - ensure it's a Series
        if "store_name" in df_shrink.columns:
            # If it's a DataFrame with multiple columns, take the first column
            if isinstance(df_shrink["store_name"], pd.DataFrame):
                df_clean["store_name"] = df_shrink["store_name"].iloc[:, 0].reset_index(drop=True)
            else:
                df_clean["store_name"] = df_shrink["store_name"].reset_index(drop=True)
        else:
            df_clean["store_name"] = "Unknown"
        
        # Extract month
        if "month" in df_shrink.columns:
            if isinstance(df_shrink["month"], pd.DataFrame):
                df_clean["month"] = df_shrink["month"].iloc[:, 0].reset_index(drop=True)
            else:
                df_clean["month"] = df_shrink["month"].reset_index(drop=True)
        else:
            df_clean["month"] = "Unknown"
        
        # Extract cause
        if "cause" in df_shrink.columns:
            if isinstance(df_shrink["cause"], pd.DataFrame):
                df_clean["cause"] = df_shrink["cause"].iloc[:, 0].reset_index(drop=True)
            else:
                df_clean["cause"] = df_shrink["cause"].reset_index(drop=True)
        else:
            df_clean["cause"] = "Unknown"
        
        # Add value_usd
        df_clean["value_usd"] = df_shrink["value_usd"].reset_index(drop=True)
        
        # Calculate totals
        total_loss = df_clean["value_usd"].sum()
        
        # Group by month
        monthly_totals = df_clean.groupby("month")["value_usd"].sum()
        avg_monthly = monthly_totals.mean() if not monthly_totals.empty else 0
        
        # Group by store_name
        store_loss = df_clean.groupby("store_name")["value_usd"].sum()
        if not store_loss.empty:
            worst_store = store_loss.idxmax()
        else:
            worst_store = "N/A"
        
        # Calculate theft losses
        theft = df_clean[df_clean["cause"] == "Theft"]["value_usd"].sum()

        kpis = [
            kpi_card("Total Losses (6mo)", f"${total_loss:,.0f}", None, None, "fa-circle-minus", "#ef4444"),
            kpi_card("Avg Monthly Loss", f"${avg_monthly:,.0f}", None, None, "fa-calendar", "#f97316"),
            kpi_card("Theft Losses", f"${theft:,.0f}", None, None, "fa-user-secret", "#8b5cf6"),
            kpi_card("Highest Loss Store", f"{worst_store[:15] if worst_store else 'N/A'}", None, None, "fa-store", "#eab308"),
        ]

        # Cause chart
        cause_totals = df_clean.groupby("cause")["value_usd"].sum().sort_values(ascending=False).reset_index()
        if not cause_totals.empty:
            colors = ["#ef4444", "#f97316", "#eab308", "#8b5cf6", "#3b82f6"]
            fig_cause = go.Figure(go.Bar(
                x=cause_totals["cause"], y=cause_totals["value_usd"],
                marker_color=colors[:len(cause_totals)]
            ))
            fig_cause.update_layout(**CHART_LAYOUT,
                                     title={"text": "Loss by Cause", "font": {"color": "#ccc", "size": 13}})
        else:
            fig_cause = go.Figure()
            fig_cause.update_layout(**CHART_LAYOUT, title={"text": "No cause data"})

        # Store chart
        store_totals = df_clean.groupby("store_name")["value_usd"].sum().sort_values(ascending=False).reset_index()
        if not store_totals.empty:
            fig_store = go.Figure(go.Bar(
                x=store_totals["value_usd"], y=store_totals["store_name"], orientation="h",
                marker_color=["#ef4444" if i == 0 else "#f97316" if i < 3 else "#3b82f6"
                              for i in range(len(store_totals))]
            ))
            store_layout = CHART_LAYOUT.copy()
            store_layout.update({
                "title": {"text": "Loss by Store", "font": {"color": "#ccc", "size": 13}},
                "yaxis": {"categoryorder": "total ascending"}
            })
            fig_store.update_layout(**store_layout)
        else:
            fig_store = go.Figure()
            fig_store.update_layout(**CHART_LAYOUT, title={"text": "No store data"})

        # Trend chart
        monthly = df_clean.groupby(["month", "cause"])["value_usd"].sum().reset_index()
        if not monthly.empty:
            fig_trend = px.bar(monthly, x="month", y="value_usd", color="cause", barmode="stack")
            fig_trend.update_layout(**CHART_LAYOUT,
                                     title={"text": "Monthly Loss Trend by Cause", "font": {"color": "#ccc", "size": 13}})
            fig_trend.update_xaxes(tickangle=-30)
        else:
            fig_trend = go.Figure()
            fig_trend.update_layout(**CHART_LAYOUT, title={"text": "No trend data"})

        return html.Div([
            page_header("Shrinkage & Loss",
                        "Theft, damage, expiry and admin errors — where inventory value disappears",
                        "fa-triangle-exclamation"),
            html.Div([
                html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                         style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
                html.Div([
                    html.Div([dcc.Graph(figure=fig_cause, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_store, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_trend, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}),
            ], style={"padding": "20px 28px"})
        ])
        
    except Exception as e:
        print(f"Error in shrinkage layout: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            page_header("Shrinkage & Loss",
                        "Theft, damage, expiry and admin errors — where inventory value disappears",
                        "fa-triangle-exclamation"),
            html.Div([
                html.Div([
                    html.Div("⚠️ Error Loading Data", style={
                        "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
                    }),
                    html.Div(str(e), style={"color": "#888", "fontSize": "14px"}),
                    html.Div("Please check that the database contains shrinkage data.",
                            style={"color": "#666", "fontSize": "12px", "marginTop": "12px"})
                ], style={"textAlign": "center", "padding": "60px"})
            ], style={"padding": "20px 28px"})
        ])
