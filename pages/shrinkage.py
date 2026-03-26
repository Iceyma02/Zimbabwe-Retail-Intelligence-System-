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

def safe_extract_store_name(value):
    """Safely extract store name from various data types"""
    if isinstance(value, (list, tuple, np.ndarray)):
        return str(value[0]) if len(value) > 0 else "Unknown"
    return str(value) if value is not None else "Unknown"

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
        
        # Make a copy and ensure all columns are simple
        df_shrink = df.copy()
        
        # Reset index completely
        df_shrink = df_shrink.reset_index(drop=True)
        
        # Ensure store_name is a simple string column - handle nested data
        if "store_name" in df_shrink.columns:
            # Apply safe extraction to handle any list/array values
            df_shrink["store_name"] = df_shrink["store_name"].apply(safe_extract_store_name)
            df_shrink["store_name"] = df_shrink["store_name"].fillna("Unknown").astype(str)
        else:
            df_shrink["store_name"] = "Unknown"
        
        # Ensure month is string
        if "month" in df_shrink.columns:
            # Extract month safely if it's a list
            if df_shrink["month"].dtype == 'object' and len(df_shrink) > 0:
                df_shrink["month"] = df_shrink["month"].apply(
                    lambda x: str(x[0]) if isinstance(x, (list, tuple, np.ndarray)) else str(x)
                )
            df_shrink["month"] = df_shrink["month"].fillna("Unknown").astype(str)
        else:
            df_shrink["month"] = "Unknown"
        
        # Ensure cause is string
        if "cause" in df_shrink.columns:
            if df_shrink["cause"].dtype == 'object' and len(df_shrink) > 0:
                df_shrink["cause"] = df_shrink["cause"].apply(
                    lambda x: str(x[0]) if isinstance(x, (list, tuple, np.ndarray)) else str(x)
                )
            df_shrink["cause"] = df_shrink["cause"].fillna("Unknown").astype(str)
        
        # Calculate totals
        total_loss = df_shrink["value_usd"].sum()
        
        # Group by month - safe grouping using observed=True
        try:
            monthly_totals = df_shrink.groupby("month", observed=True)["value_usd"].sum()
            avg_monthly = monthly_totals.mean() if not monthly_totals.empty else 0
        except Exception as e:
            print(f"Error grouping by month: {e}")
            avg_monthly = 0
        
        # Group by store_name - safe grouping using observed=True
        try:
            # Use the string column directly
            store_loss = df_shrink.groupby(df_shrink["store_name"], observed=True)["value_usd"].sum()
            if not store_loss.empty:
                worst_store = store_loss.idxmax()
                worst_store_value = store_loss.max()
            else:
                worst_store = "N/A"
        except Exception as e:
            print(f"Error grouping by store_name: {e}")
            worst_store = "N/A"
        
        # Calculate theft losses
        if "cause" in df_shrink.columns:
            theft = df_shrink[df_shrink["cause"] == "Theft"]["value_usd"].sum()
        else:
            theft = 0

        kpis = [
            kpi_card("Total Losses (6mo)", f"${total_loss:,.0f}", None, None, "fa-circle-minus", "#ef4444"),
            kpi_card("Avg Monthly Loss", f"${avg_monthly:,.0f}", None, None, "fa-calendar", "#f97316"),
            kpi_card("Theft Losses", f"${theft:,.0f}", None, None, "fa-user-secret", "#8b5cf6"),
            kpi_card("Highest Loss Store", f"{worst_store[:15] if worst_store else 'N/A'}", None, None, "fa-store", "#eab308"),
        ]

        # Cause chart
        if "cause" in df_shrink.columns:
            try:
                cause_totals = df_shrink.groupby("cause", observed=True)["value_usd"].sum().sort_values(ascending=False).reset_index()
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
            except Exception as e:
                print(f"Error creating cause chart: {e}")
                fig_cause = go.Figure()
                fig_cause.update_layout(**CHART_LAYOUT, title={"text": f"Error: {str(e)[:50]}"})
        else:
            fig_cause = go.Figure()
            fig_cause.update_layout(**CHART_LAYOUT, title={"text": "No cause column"})

        # Store chart - using safe grouping
        try:
            # Use the string column directly for grouping
            store_totals = df_shrink.groupby(df_shrink["store_name"], observed=True)["value_usd"].sum().sort_values(ascending=False)
            store_totals_df = store_totals.reset_index()
            store_totals_df.columns = ["store_name", "value_usd"]
            
            if not store_totals_df.empty:
                fig_store = go.Figure(go.Bar(
                    x=store_totals_df["value_usd"], y=store_totals_df["store_name"], orientation="h",
                    marker_color=["#ef4444" if i == 0 else "#f97316" if i < 3 else "#3b82f6"
                                  for i in range(len(store_totals_df))]
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
        except Exception as e:
            print(f"Error creating store chart: {e}")
            fig_store = go.Figure()
            fig_store.update_layout(**CHART_LAYOUT, title={"text": f"Error: {str(e)[:50]}"})

        # Trend chart
        if "month" in df_shrink.columns and "cause" in df_shrink.columns:
            try:
                monthly = df_shrink.groupby(["month", "cause"], observed=True)["value_usd"].sum().reset_index()
                if not monthly.empty:
                    fig_trend = px.bar(monthly, x="month", y="value_usd", color="cause", barmode="stack")
                    fig_trend.update_layout(**CHART_LAYOUT,
                                             title={"text": "Monthly Loss Trend by Cause", "font": {"color": "#ccc", "size": 13}})
                    fig_trend.update_xaxes(tickangle=-30)
                else:
                    fig_trend = go.Figure()
                    fig_trend.update_layout(**CHART_LAYOUT, title={"text": "No trend data"})
            except Exception as e:
                print(f"Error creating trend chart: {e}")
                fig_trend = go.Figure()
                fig_trend.update_layout(**CHART_LAYOUT, title={"text": f"Error: {str(e)[:50]}"})
        else:
            fig_trend = go.Figure()
            fig_trend.update_layout(**CHART_LAYOUT, title={"text": "Missing month or cause columns"})

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
