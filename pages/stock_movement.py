"""Stock Movement Intelligence — Page 6 with Retailer Filter"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/stock-movement", name="Stock Movement", order=5)

def layout():
    return html.Div([
        page_header("Stock Movement Intelligence",
                    "Why is stock moving — sales, deliveries, damage, theft breakdown", "fa-arrow-trend-up"),
        html.Div(id="stock-movement-content", style={"padding": "20px 28px"})
    ])


@callback(
    Output("stock-movement-content", "children"),
    Input("active-retailer", "data")
)
def update_stock_movement(retailer):
    try:
        df = get_sales(90, retailer)
        
        if df.empty:
            return html.Div([
                html.Div("No stock movement data available", 
                        style={"textAlign": "center", "padding": "60px", "color": "#888"})
            ])
        
        retailer_name = retailer if retailer != "ALL" else "All Retailers"
        
        df["date"] = pd.to_datetime(df["date"])
        df["week"] = df["date"].dt.to_period("W").astype(str)

        weekly = df.groupby("week").agg(revenue=("revenue","sum"), units=("units_sold","sum")).reset_index()
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=weekly["week"], y=weekly["units"], name="Units Sold",
                               marker_color="#3b82f6", opacity=0.8))
        fig1.update_layout(**CHART_LAYOUT,
                            title={"text": f"Weekly Stock Movement (Units Sold) - {retailer_name}", "font": {"color": "#ccc", "size": 13}})
        fig1.update_xaxes(tickangle=-45, nticks=12)

        cat_weekly = df.groupby(["week", "category"])["units_sold"].sum().reset_index()
        fig2 = px.line(cat_weekly, x="week", y="units_sold", color="category")
        fig2.update_layout(**CHART_LAYOUT,
                            title={"text": f"Units Moved by Category (Weekly) - {retailer_name}", "font": {"color": "#ccc", "size": 13}})
        fig2.update_xaxes(nticks=8)

        store_cat = df.groupby(["store_name", "category"])["units_sold"].sum().reset_index()
        pivot = store_cat.pivot(index="store_name", columns="category", values="units_sold").fillna(0)
        fig3 = go.Figure(go.Heatmap(
            z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
            colorscale=[[0, "#0d0d0d"], [0.5, "#00c853"], [1, "#88ffbb"]],
            showscale=True
        ))
        fig3.update_layout(**CHART_LAYOUT,
                            title={"text": f"Store × Category Sales Heatmap - {retailer_name}", "font": {"color": "#ccc", "size": 13}})

        return html.Div([
            html.Div([dcc.Graph(figure=fig1, config={"displayModeBar": False}, style={"height": "320px"})],
                     style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px",
                            "padding": "16px", "marginBottom": "14px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig2, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                                "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig3, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                                "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px"}),
        ])
        
    except Exception as e:
        print(f"Error in stock movement: {e}")
        return html.Div([
            html.Div("⚠️ Error Loading Data", style={
                "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
            }),
            html.Div(str(e), style={"color": "#888", "fontSize": "14px"})
        ], style={"textAlign": "center", "padding": "60px"})
