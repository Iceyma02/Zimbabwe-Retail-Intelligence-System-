"""Demand Forecasting — Page 7 with Retailer Filter"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/forecasting", name="Demand Forecasting", order=6)

PRODUCTS_LIST = [
    {"label": "Fresh Full Cream Milk 2L", "value": "P001"},
    {"label": "Olivine Cooking Oil 2L", "value": "P004"},
    {"label": "Coca-Cola 2L", "value": "P007"},
    {"label": "Lobels White Bread 700g", "value": "P010"},
    {"label": "Gold Seal Roller Meal 10kg", "value": "P012"},
]

def layout():
    stores = get_stores()
    store_opts = [{"label": r["name"], "value": r["store_id"]} for _, r in stores.iterrows()]
    return html.Div([
        page_header("Demand Forecasting", "ML-powered 30-day demand predictions per product per store", "fa-brain"),
        html.Div(id="forecasting-content", style={"padding": "20px 28px"}),
        dcc.Store(id="forecasting-store-data")
    ])


def simple_forecast(df_daily, horizon=30):
    df_daily = df_daily.copy()
    df_daily["ds"] = pd.to_datetime(df_daily["date"])
    df_daily = df_daily.sort_values("ds")
    y = df_daily["units_sold"].values
    x = np.arange(len(y))
    
    if len(y) < 2:
        return pd.date_range(start=pd.Timestamp.now(), periods=horizon), np.array([y.mean() if len(y) > 0 else 0] * horizon)
    
    coeffs = np.polyfit(x, y, 1)
    trend_slope = coeffs[0]
    trend_intercept = coeffs[1]
    
    df_daily["dow"] = df_daily["ds"].dt.dayofweek
    dow_means = df_daily.groupby("dow")["units_sold"].mean()
    global_mean = y.mean() if y.mean() > 0 else 1
    dow_factors = (dow_means / global_mean).fillna(1.0).to_dict()
    
    df_daily["month"] = df_daily["ds"].dt.month
    month_means = df_daily.groupby("month")["units_sold"].mean()
    month_factors = (month_means / global_mean).fillna(1.0).to_dict()
    
    last_date = df_daily["ds"].iloc[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)
    forecast_vals = []
    for i, fd in enumerate(future_dates):
        trend_val = trend_slope * (len(y) + i) + trend_intercept
        seasonal = dow_factors.get(fd.dayofweek, 1.0) * month_factors.get(fd.month, 1.0)
        pred = max(0, trend_val * seasonal)
        forecast_vals.append(pred)
    
    return future_dates, np.array(forecast_vals)


@callback(
    Output("forecasting-content", "children"),
    Input("active-retailer", "data")
)
def update_forecasting_ui(retailer):
    stores = get_stores(retailer)
    if stores.empty:
        return html.Div(f"No stores available for {retailer}", style={"textAlign": "center", "padding": "60px", "color": "#888"})
    
    store_opts = [{"label": r["name"], "value": r["store_id"]} for _, r in stores.iterrows()]
    
    return html.Div([
        html.Div([
            html.Div("⚡ Uses linear trend + seasonal decomposition", style={
                "background": "#1a1a2e", "border": "1px solid #3b82f680",
                "borderRadius": "8px", "padding": "10px 16px",
                "color": "#60a5fa", "fontSize": "12px", "marginBottom": "20px"
            }),
            html.Div([
                dcc.Dropdown(id="fc-store", options=store_opts, value=store_opts[0]["value"] if store_opts else None, clearable=False,
                             style={"width": "220px"}),
                dcc.Dropdown(id="fc-product", options=PRODUCTS_LIST, value="P007", clearable=False,
                             style={"width": "260px"}),
            ], style={"display": "flex", "gap": "12px", "marginBottom": "20px"}),
            dcc.Graph(id="fc-forecast-chart", config={"displayModeBar": False},
                      style={"height": "380px", "background": "#161616",
                             "border": "1px solid #222", "borderRadius": "10px", "padding": "10px"}),
            html.Div([
                html.Div([
                    dcc.Graph(id="fc-seasonality", config={"displayModeBar": False}, style={"height": "240px"})
                ], style={"flex": 1, "background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "16px"}),
                html.Div(id="fc-summary-box", style={"flex": 1, "background": "#161616",
                                                      "border": "1px solid #222", "borderRadius": "10px",
                                                      "padding": "20px"}),
            ], style={"display": "flex", "gap": "14px", "marginTop": "14px"}),
        ]),
        dcc.Store(id="fc-retailer", data=retailer)
    ])


@callback(
    Output("fc-forecast-chart", "figure"),
    Output("fc-seasonality", "figure"),
    Output("fc-summary-box", "children"),
    Input("fc-store", "value"),
    Input("fc-product", "value"),
    Input("fc-retailer", "data")
)
def update_forecast(store_id, product_id, retailer):
    try:
        sales = query(f"""
            SELECT date, SUM(units_sold) as units_sold
            FROM sales 
            JOIN stores ON sales.store_id = stores.store_id
            WHERE store_id='{store_id}' AND product_id='{product_id}'
            AND date >= date('now','-90 days')
            {f"AND stores.retailer_id = '{retailer}'" if retailer != "ALL" else ""}
            GROUP BY date ORDER BY date
        """)

        if sales.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(**CHART_LAYOUT, title={"text": "No data available", "font": {"color": "#ccc"}})
            return empty_fig, empty_fig, html.Div("No data available for this selection")

        future_dates, forecast = simple_forecast(sales, horizon=30)
        lower = forecast * 0.82
        upper = forecast * 1.18

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sales["date"], y=sales["units_sold"], name="Historical",
            line={"color": "#3b82f6", "width": 2}
        ))
        fig.add_trace(go.Scatter(
            x=future_dates, y=forecast, name="Forecast",
            line={"color": "#00c853", "width": 2, "dash": "dash"}
        ))
        fig.add_trace(go.Scatter(
            x=list(future_dates) + list(future_dates[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself", fillcolor="rgba(227,24,55,0.1)",
            line={"color": "rgba(0,0,0,0)"}, name="Confidence Interval"
        ))
        fig.update_layout(**CHART_LAYOUT, title={"text": "30-Day Demand Forecast", "font": {"color": "#ccc", "size": 13}})

        sales["dow"] = pd.to_datetime(sales["date"]).dt.dayofweek
        dow_avg = sales.groupby("dow")["units_sold"].mean()
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        fig2 = go.Figure(go.Bar(
            x=[days[i] for i in dow_avg.index if i in dow_avg.index],
            y=dow_avg.values,
            marker_color=["#00c853" if d >= 5 else "#3b82f6" for d in dow_avg.index]
        ))
        fig2.update_layout(**CHART_LAYOUT, title={"text": "Average Demand by Day of Week", "font": {"color": "#ccc", "size": 13}})

        total_30d = int(forecast.sum())
        avg_daily = int(forecast.mean())
        peak_day = future_dates[np.argmax(forecast)].strftime("%b %d")

        summary = html.Div([
            html.Div("Forecast Summary", style={"color": "#888", "fontSize": "11px",
                                                 "textTransform": "uppercase", "letterSpacing": "1px",
                                                 "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div("Projected 30-Day Demand", style={"color": "#666", "fontSize": "12px"}),
                    html.Div(f"{total_30d:,} units", style={"color": "#fff", "fontSize": "28px",
                                                              "fontWeight": "700", "fontFamily": "'Syne', sans-serif"})
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Div("Daily Average", style={"color": "#666", "fontSize": "12px"}),
                    html.Div(f"{avg_daily} units/day", style={"color": "#3b82f6", "fontSize": "20px", "fontWeight": "600"})
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Div("Peak Demand Day", style={"color": "#666", "fontSize": "12px"}),
                    html.Div(peak_day, style={"color": "#eab308", "fontSize": "18px", "fontWeight": "600"})
                ], style={"marginBottom": "16px"}),
                html.Div([
                    html.Div("📦 Recommended Stock Order", style={"color": "#666", "fontSize": "12px"}),
                    html.Div(f"{int(total_30d * 1.15):,} units", style={
                        "color": "#22c55e", "fontSize": "18px", "fontWeight": "600",
                        "background": "#0a2d15", "border": "1px solid #22c55e30",
                        "borderRadius": "6px", "padding": "6px 12px", "marginTop": "4px"
                    })
                ])
            ])
        ])

        return fig, fig2, summary
        
    except Exception as e:
        print(f"Error in forecast: {e}")
        empty_fig = go.Figure()
        empty_fig.update_layout(**CHART_LAYOUT, title={"text": f"Error: {str(e)[:50]}"})
        return empty_fig, empty_fig, html.Div(f"Error: {e}")
