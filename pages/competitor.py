"""Competitor Price Watch — Page 12 with Retailer Filter"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/competitor", name="Competitor Watch", order=11)

def layout():
    return html.Div([
        page_header("Competitor Price Watch",
                    "How prices compare across TM Pick n Pay, OK Zimbabwe, Spar, SaiMart & Choppies", "fa-store"),
        html.Div(id="competitor-content", style={"padding": "20px 28px"})
    ])


@callback(
    Output("competitor-content", "children"),
    Input("active-retailer", "data")
)
def update_competitor(retailer):
    try:
        df = get_competitor_prices()
        
        if df.empty:
            return html.Div([
                html.Div("No competitor price data available", 
                        style={"textAlign": "center", "padding": "60px", "color": "#888"})
            ])
        
        retailer_name = retailer if retailer != "ALL" else "All Retailers"
        
        if "base_price" in df.columns and "pnp_price" not in df.columns:
            df = df.rename(columns={"base_price": "pnp_price", "retailer": "competitor", "retailer_price": "competitor_price"})

        df["pnp_cheaper"] = df["pnp_price"] > df["competitor_price"]
        win_rate = len(df[df["pnp_cheaper"]]) / len(df) * 100
        avg_diff = df["price_diff"].mean()

        kpis = [
            kpi_card("Price Win Rate", f"{win_rate:.0f}%", None, None, "fa-trophy", "#22c55e"),
            kpi_card("Avg Price Diff", f"${avg_diff:+.2f}", None, None, "fa-scale-balanced",
                     "#22c55e" if avg_diff > 0 else "#ef4444"),
            kpi_card("Products Tracked", str(df["product_id"].nunique()), None, None, "fa-boxes-stacked", "#3b82f6"),
            kpi_card("Retailers", str(df["competitor"].nunique()), None, None, "fa-store", "#8b5cf6"),
        ]

        pivot = df.pivot_table(index="product_name", columns="competitor", values="price_diff", aggfunc="mean")
        pivot.index = [n[:22] for n in pivot.index]
        fig_matrix = go.Figure(go.Heatmap(
            z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
            colorscale=[[0, "#22c55e"], [0.5, "#1a1a1a"], [1, "#ef4444"]],
            text=[[f"${v:+.2f}" for v in row] for row in pivot.values],
            texttemplate="%{text}", showscale=True,
            colorbar={"title": "Price Diff ($)", "titlefont": {"color": "#888"}, "tickfont": {"color": "#888"}}
        ))
        fig_matrix.update_layout(**CHART_LAYOUT,
                                  title={"text": f"Price Difference Matrix - {retailer_name} (green = cheaper competitor)", "font": {"color": "#ccc", "size": 13}})

        win_by_comp = df.groupby("competitor")["pnp_cheaper"].mean().reset_index()
        win_by_comp["win_pct"] = win_by_comp["pnp_cheaper"] * 100
        fig_win = go.Figure(go.Bar(
            x=win_by_comp["competitor"], y=win_by_comp["win_pct"],
            marker_color=["#22c55e" if w > 50 else "#ef4444" for w in win_by_comp["win_pct"]],
            text=win_by_comp["win_pct"].apply(lambda x: f"{x:.0f}%"), textposition="outside"
        ))
        fig_win.add_hline(y=50, line_dash="dash", line_color="#666", annotation_text="50% baseline")
        fig_win.update_layout(**CHART_LAYOUT,
                               title={"text": f"% Products Where Base Price is Cheaper - {retailer_name}", "font": {"color": "#ccc", "size": 13}},
                               yaxis_range=[0, 115])

        headers = ["Product", "Category", "Base Price", "Competitor", "Their Price", "Difference", "Cheaper?"]
        header_row = html.Tr([html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "7px 10px",
                                                 "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                              for h in headers])
        rows = []
        for _, row in df.sort_values("price_diff").iterrows():
            diff_color = "#22c55e" if row["pnp_cheaper"] else "#ef4444"
            rows.append(html.Tr([
                html.Td(row["product_name"][:28], style={"color": "#ddd", "padding": "6px 10px", "fontSize": "12px"}),
                html.Td(row["category"], style={"color": "#888", "padding": "6px 10px", "fontSize": "11px"}),
                html.Td(f"${row['pnp_price']:.2f}", style={"color": "#fff", "padding": "6px 10px", "fontWeight": "600"}),
                html.Td(row["competitor"], style={"color": "#888", "padding": "6px 10px"}),
                html.Td(f"${row['competitor_price']:.2f}", style={"color": "#aaa", "padding": "6px 10px"}),
                html.Td(f"${row['price_diff']:+.2f}", style={"color": diff_color, "padding": "6px 10px", "fontWeight": "600"}),
                html.Td("✅ Yes" if row["pnp_cheaper"] else "❌ No",
                        style={"color": diff_color, "padding": "6px 10px", "fontWeight": "600"}),
            ], style={"borderBottom": "1px solid #1a1a1a"}))

        table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                           style={"width": "100%", "borderCollapse": "collapse"})

        return html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_matrix, config={"displayModeBar": False}, style={"height": "380px"})],
                         style={"flex": "1.5", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_win, config={"displayModeBar": False}, style={"height": "380px"})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px"}),
            html.Div([
                html.Div("Price Comparison Detail", style={"color": "#888", "fontSize": "11px",
                                                            "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "14px"}),
                table
            ], style={"background": "#161616", "border": "1px solid #222", "borderRadius": "10px", "padding": "20px", "overflowX": "auto"}),
        ])
        
    except Exception as e:
        print(f"Error in competitor: {e}")
        return html.Div([
            html.Div("⚠️ Error Loading Data", style={
                "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
            }),
            html.Div(str(e), style={"color": "#888", "fontSize": "14px"})
        ], style={"textAlign": "center", "padding": "60px"})
