"""Zimbabwe Market Watch — Page 16"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/market-watch", name="Market Watch", order=15)

SEASONAL_EVENTS = [
    {"month": 1,  "event": "January — Post-Christmas Slump",         "impact": "LOW",      "note": "Consumer wallets tight after December spending"},
    {"month": 2,  "event": "February — Valentine's & Back to School", "impact": "MEDIUM",   "note": "School supply demand spikes, confectionery up"},
    {"month": 4,  "event": "April — Easter Bonanza",                  "impact": "HIGH",     "note": "Biggest trading weekend of Q1, stock up early"},
    {"month": 4,  "event": "April 18 — Independence Day",             "impact": "HIGH",     "note": "Braai & social gathering products spike 40%+"},
    {"month": 6,  "event": "June/July — Winter Warmers",              "impact": "MEDIUM",   "note": "Hot beverages, soups and comfort foods up"},
    {"month": 8,  "event": "August — Zimbabwe Heroes Day",            "impact": "MEDIUM",   "note": "Long weekend drives higher store footfall"},
    {"month": 9,  "event": "September — Spring/Mid-term",             "impact": "LOW",      "note": "Quiet period — good time for stocktaking"},
    {"month": 11, "event": "November — Pre-Christmas Build",          "impact": "HIGH",     "note": "Start Christmas stock build-up now"},
    {"month": 12, "event": "December — Peak Season",                  "impact": "CRITICAL", "note": "Highest demand month. Double safety stock across all categories"},
]

def layout():
    try:
        df = get_economic_indicators()
        
        if df.empty:
            return html.Div([
                page_header("Zimbabwe Market Watch",
                            "Exchange rates, inflation, fuel, load shedding — local factors affecting retail", "fa-globe-africa"),
                html.Div([
                    html.Div("No economic data available", 
                            style={"textAlign": "center", "padding": "60px", "color": "#888"})
                ], style={"padding": "20px 28px"})
            ])
        
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        latest = df.iloc[-1]

        forex_colors = {"HIGH": "#22c55e", "MEDIUM": "#eab308", "LOW": "#f97316", "CRITICAL": "#ef4444"}
        forex_color = forex_colors.get(latest["forex_availability"], "#888")

        # Live strip
        indicators = [
            {"label": "USD/ZiG Rate",       "value": f"{latest['usd_zig_rate']:.2f}",             "color": "#eab308", "icon": "fa-money-bill-wave"},
            {"label": "Fuel (USD/L)",        "value": f"${latest['fuel_price_usd_per_litre']:.3f}", "color": "#f97316", "icon": "fa-gas-pump"},
            {"label": "Inflation Rate",      "value": f"{latest['inflation_rate_percent']:.1f}%",   "color": "#ef4444", "icon": "fa-arrow-trend-up"},
            {"label": "Load Shedding",       "value": f"{int(latest['load_shedding_hours'])}h/day", "color": "#8b5cf6", "icon": "fa-bolt"},
            {"label": "Forex Availability",  "value": latest["forex_availability"],                  "color": forex_color, "icon": "fa-coins"},
        ]
        strip = html.Div([
            html.Div([
                html.I(className=f"fa-solid {ind['icon']}",
                       style={"color": ind["color"], "fontSize": "16px", "marginRight": "10px"}),
                html.Div([
                    html.Div(ind["label"], style={"color": "#666", "fontSize": "10px",
                                                   "textTransform": "uppercase", "letterSpacing": "0.8px"}),
                    html.Div(ind["value"], style={"color": "#fff", "fontSize": "18px", "fontWeight": "700",
                                                   "fontFamily": "'Syne', sans-serif"})
                ])
            ], style={"flex": 1, "display": "flex", "alignItems": "center",
                      "background": "#161616", "border": f"1px solid {ind['color']}30",
                      "borderRadius": "8px", "padding": "14px 16px"})
            for ind in indicators
        ], style={"display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap"})

        # ZiG rate
        fig_zig = go.Figure(go.Scatter(x=df["date"], y=df["usd_zig_rate"],
                                        line={"color": "#eab308", "width": 2},
                                        fill="tozeroy", fillcolor="rgba(234,179,8,0.07)"))
        fig_zig.update_layout(**CHART_LAYOUT, title={"text": "USD / ZiG Rate (180 Days)", "font": {"color": "#ccc", "size": 13}})

        # Inflation
        fig_inf = go.Figure(go.Scatter(x=df["date"], y=df["inflation_rate_percent"],
                                        line={"color": "#ef4444", "width": 2},
                                        fill="tozeroy", fillcolor="rgba(239,68,68,0.07)"))
        fig_inf.update_layout(**CHART_LAYOUT, title={"text": "Inflation Rate % (180 Days)", "font": {"color": "#ccc", "size": 13}})

        # Fuel
        fig_fuel = go.Figure(go.Scatter(x=df["date"], y=df["fuel_price_usd_per_litre"],
                                         line={"color": "#f97316", "width": 2},
                                         fill="tozeroy", fillcolor="rgba(249,115,22,0.07)"))
        fig_fuel.update_layout(**CHART_LAYOUT, title={"text": "Fuel Price USD/Litre (180 Days)", "font": {"color": "#ccc", "size": 13}})

        # Load shedding - FIXED: Removed alpha channel from color
        weekly_ls = df.set_index("date").resample("W")["load_shedding_hours"].mean().reset_index()
        ls_colors = ["#ef4444" if h > 8 else "#f97316" if h > 4 else "#22c55e" for h in weekly_ls["load_shedding_hours"]]
        fig_ls = go.Figure(go.Bar(x=weekly_ls["date"], y=weekly_ls["load_shedding_hours"], marker_color=ls_colors))
        fig_ls.add_hline(y=8, line_dash="dash", line_color="#ef4444", annotation_text="Critical (8h)")
        fig_ls.update_layout(**CHART_LAYOUT, title={"text": "Weekly Avg Load Shedding Hours", "font": {"color": "#ccc", "size": 13}})

        # Seasonal calendar
        impact_colors = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        calendar_items = [
            html.Div("📅 Zimbabwe Retail Seasonal Calendar", style={
                "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                "letterSpacing": "1px", "marginBottom": "14px"
            })
        ]
        for event in SEASONAL_EVENTS:
            color = impact_colors.get(event["impact"], "#888")
            calendar_items.append(html.Div([
                html.Div([
                    html.Span(f"Month {event['month']:02d}", style={"color": "#555", "fontSize": "10px", "width": "52px"}),
                    html.Span(event["event"], style={"color": "#ddd", "fontSize": "12px", "fontWeight": "500", "flex": 1}),
                    html.Span(event["impact"], style={
                        "color": color, "fontSize": "10px", "fontWeight": "700",
                        "background": f"{color}15", "border": f"1px solid {color}30",
                        "borderRadius": "4px", "padding": "1px 6px"
                    })
                ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
                html.Div(event["note"], style={"color": "#555", "fontSize": "11px", "marginTop": "2px", "marginLeft": "60px"})
            ], style={"padding": "8px 0", "borderBottom": "1px solid #1a1a1a"}))

        return html.Div([
            page_header("Zimbabwe Market Watch",
                        "Exchange rates, inflation, fuel, load shedding — local factors affecting retail", "fa-globe-africa"),
            html.Div([
                strip,
                html.Div([
                    html.Div([dcc.Graph(figure=fig_zig, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_inf, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div([dcc.Graph(figure=fig_fuel, config={"displayModeBar": False}, style={"height": "280px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                ], style={"display": "flex", "gap": "14px", "marginBottom": "14px", "flexWrap": "wrap"}),
                html.Div([
                    html.Div([dcc.Graph(figure=fig_ls, config={"displayModeBar": False}, style={"height": "240px"})],
                             style={"flex": 1, "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                    html.Div(calendar_items,
                             style={"flex": "1.4", "background": "#161616", "border": "1px solid #222",
                                    "borderRadius": "10px", "padding": "20px"}),
                ], style={"display": "flex", "gap": "14px"}),
            ], style={"padding": "20px 28px"})
        ])
        
    except Exception as e:
        print(f"Error in market watch layout: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            page_header("Zimbabwe Market Watch",
                        "Exchange rates, inflation, fuel, load shedding — local factors affecting retail", "fa-globe-africa"),
            html.Div([
                html.Div([
                    html.Div("⚠️ Error Loading Data", style={
                        "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
                    }),
                    html.Div(str(e), style={"color": "#888", "fontSize": "14px"}),
                    html.Div("Please check that the database contains economic data.",
                            style={"color": "#666", "fontSize": "12px", "marginTop": "12px"})
                ], style={"textAlign": "center", "padding": "60px"})
            ], style={"padding": "20px 28px"})
        ])
