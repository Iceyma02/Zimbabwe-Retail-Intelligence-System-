"""National Overview - Page 1 - Enhanced with Modern Styling"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db import (
    get_national_kpis, get_category_sales, get_daily_trend, 
    get_store_revenue_summary, get_inventory_simple, get_supplier_credit
)
from components.shared import page_header, kpi_card, status_badge, CHART_LAYOUT

# Retailer name mapping
RETAILER_NAMES = {
    "ALL": "All Retailers",
    "PNP": "TM Pick n Pay",
    "OK": "OK Zimbabwe",
    "SPAR": "Spar Zimbabwe",
    "SAIMART": "SaiMart",
    "CHOPPIES": "Choppies Zimbabwe",
}

dash.register_page(__name__, path="/", name="National Overview", order=0)

def layout():
    return html.Div([
        page_header("National Overview", "Real-time performance across all Zimbabwe stores", "fa-gauge-high"),
        html.Div([
            # KPI Cards Row
            html.Div(id="overview-kpis", style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            
            # Charts Row
            html.Div([
                html.Div([
                    dcc.Graph(id="overview-trend", config={"displayModeBar": False, "responsive": True}, style={"height": "320px"})
                ], style={"flex": "2", "background": "rgba(22, 22, 22, 0.6)", "backdropFilter": "blur(10px)",
                          "border": "1px solid rgba(255,255,255,0.05)", "borderRadius": "16px", "padding": "20px"}),
                html.Div([
                    dcc.Graph(id="overview-category", config={"displayModeBar": False, "responsive": True}, style={"height": "320px"})
                ], style={"flex": "1", "background": "rgba(22, 22, 22, 0.6)", "backdropFilter": "blur(10px)",
                          "border": "1px solid rgba(255,255,255,0.05)", "borderRadius": "16px", "padding": "20px"}),
            ], style={"display": "flex", "gap": "20px", "marginBottom": "20px", "flexWrap": "wrap"}),
            
            # Store Ranking & Alerts Row
            html.Div([
                html.Div([
                    html.Div(id="store-ranking-header", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px", "fontWeight": "600"
                    }),
                    html.Div(id="store-ranking-list", style={"maxHeight": "400px", "overflowY": "auto"})
                ], style={"flex": "1", "background": "rgba(22, 22, 22, 0.6)", "backdropFilter": "blur(10px)",
                          "border": "1px solid rgba(255,255,255,0.05)", "borderRadius": "16px", "padding": "20px"}),
                html.Div([
                    html.Div("🚨 Active Alerts", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px", "fontWeight": "600"
                    }),
                    html.Div(id="active-alerts", style={"maxHeight": "400px", "overflowY": "auto"})
                ], style={"flex": "1", "background": "rgba(22, 22, 22, 0.6)", "backdropFilter": "blur(10px)",
                          "border": "1px solid rgba(255,255,255,0.05)", "borderRadius": "16px", "padding": "20px"}),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
        ], style={"padding": "20px 28px"}),
        dcc.Interval(id="overview-refresh", interval=300000, n_intervals=0)  # 5 minute refresh
    ])


@callback(
    Output("overview-kpis", "children"),
    Output("overview-trend", "figure"),
    Output("overview-category", "figure"),
    Output("store-ranking-list", "children"),
    Output("store-ranking-header", "children"),
    Output("active-alerts", "children"),
    Input("active-retailer", "data"),
    Input("overview-refresh", "n_intervals")
)
def update_overview(retailer, _):
    """Update all overview components when retailer changes or interval triggers"""
    try:
        retailer_name = RETAILER_NAMES.get(retailer, "All Retailers")
        
        # Get KPIs
        kpis = get_national_kpis(30, retailer)
        if kpis.empty:
            revenue = profit = units = margin = 0
        else:
            revenue = kpis["total_revenue"].iloc[0]
            profit = kpis["total_profit"].iloc[0]
            units = kpis["total_units"].iloc[0]
            margin = kpis["margin_pct"].iloc[0]
        
        # Get previous period for comparison
        kpis_prev = get_national_kpis(60, retailer)
        if kpis_prev.empty:
            prev_revenue = revenue
        else:
            prev_revenue = kpis_prev["total_revenue"].iloc[0]
        
        rev_delta = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Inventory alerts
        inv = get_inventory_simple(retailer)
        critical_count = len(inv[inv["status"] == "CRITICAL"]) if not inv.empty else 0
        low_count = len(inv[inv["status"] == "LOW"]) if not inv.empty else 0
        
        # Create KPI Cards with enhanced styling
        kpi_cards = [
            html.Div(kpi_card("30-Day Revenue", f"${revenue:,.0f}", rev_delta, "vs prev 30d", "fa-dollar-sign", "#00c853"), 
                    style={"flex": 1, "minWidth": "150px"}),
            html.Div(kpi_card("30-Day Profit", f"${profit:,.0f}", None, None, "fa-chart-line", "#22c55e"), 
                    style={"flex": 1, "minWidth": "150px"}),
            html.Div(kpi_card("Profit Margin", f"{margin:.1f}%", None, None, "fa-percent", "#3b82f6"), 
                    style={"flex": 1, "minWidth": "150px"}),
            html.Div(kpi_card("Units Sold", f"{units:,}", None, None, "fa-box", "#8b5cf6"), 
                    style={"flex": 1, "minWidth": "150px"}),
            html.Div(kpi_card("Critical Stock", str(critical_count), None, None, "fa-triangle-exclamation", "#ef4444"), 
                    style={"flex": 1, "minWidth": "150px"}),
            html.Div(kpi_card("Low Stock Items", str(low_count), None, None, "fa-exclamation", "#f97316"), 
                    style={"flex": 1, "minWidth": "150px"}),
        ]
        
        # Enhanced Trend Chart - FIXED: No duplicate hovermode
        trend_df = get_daily_trend(60, retailer)
        fig_trend = go.Figure()
        
        if not trend_df.empty:
            # Add Revenue line with gradient fill
            fig_trend.add_trace(go.Scatter(
                x=trend_df["date"], 
                y=trend_df["revenue"], 
                name="Revenue",
                line={"color": "#00c853", "width": 3},
                fill="tozeroy",
                fillcolor="rgba(0,200,83,0.15)",
                hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>"
            ))
            
            # Add Profit line
            fig_trend.add_trace(go.Scatter(
                x=trend_df["date"], 
                y=trend_df["profit"], 
                name="Profit",
                line={"color": "#22c55e", "width": 2, "dash": "dot"},
                hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>"
            ))
        
        # Modern layout for trend chart - FIXED: Removed duplicate hovermode
        trend_layout = CHART_LAYOUT.copy()
        trend_layout.update({
            "title": {
                "text": f"60-Day Revenue & Profit Trend - {retailer_name}",
                "font": {"color": "#fff", "size": 14, "family": "Syne"},
                "x": 0.05,
                "xanchor": "left"
            },
            "plot_bgcolor": "#0d0d0d",
            "xaxis": {
                "showgrid": True,
                "gridcolor": "#1e1e1e",
                "gridwidth": 0.5,
                "showline": True,
                "linecolor": "#2a2a2a",
                "title": None
            },
            "yaxis": {
                "showgrid": True,
                "gridcolor": "#1e1e1e",
                "gridwidth": 0.5,
                "showline": True,
                "linecolor": "#2a2a2a",
                "title": {"text": "Amount ($)", "font": {"color": "#888", "size": 11}}
            },
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
                "bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#aaa"}
            },
            "margin": {"t": 60, "b": 40, "l": 50, "r": 30}
        })
        fig_trend.update_layout(**trend_layout)
        
        # Enhanced Category Chart
        cat_df = get_category_sales(30, retailer)
        if not cat_df.empty:
            # Sort by revenue for better visualization
            cat_df = cat_df.sort_values("revenue", ascending=True)
            
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(
                x=cat_df["revenue"],
                y=cat_df["category"],
                orientation="h",
                marker=dict(
                    color=cat_df["revenue"],
                    colorscale=[
                        [0, "#2d0a0a"],
                        [0.5, "#f97316"],
                        [1, "#00c853"]
                    ],
                    showscale=True,
                    colorbar={
                        "title": "Revenue ($)",
                        "titlefont": {"color": "#888"},
                        "tickfont": {"color": "#888"},
                        "x": 1.02
                    }
                ),
                text=cat_df["revenue"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
                textfont={"size": 10, "color": "#aaa"},
                hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
            ))
            
            category_layout = CHART_LAYOUT.copy()
            category_layout.update({
                "title": {
                    "text": f"Revenue by Category - {retailer_name}",
                    "font": {"color": "#fff", "size": 14, "family": "Syne"},
                    "x": 0.05,
                    "xanchor": "left"
                },
                "xaxis": {
                    "title": {"text": "Revenue ($)", "font": {"color": "#888", "size": 11}},
                    "tickprefix": "$",
                    "showgrid": True,
                    "gridcolor": "#1e1e1e"
                },
                "yaxis": {
                    "title": None,
                    "showgrid": False,
                    "categoryorder": "total ascending"
                },
                "height": 350,
                "margin": {"t": 60, "b": 20, "l": 120, "r": 60}
            })
            fig_cat.update_layout(**category_layout)
        else:
            fig_cat = go.Figure()
            fig_cat.update_layout(
                **CHART_LAYOUT,
                title={
                    "text": f"No category data available - {retailer_name}",
                    "font": {"color": "#888", "size": 14}
                }
            )
        
        # Store ranking with enhanced styling
        store_df = get_store_revenue_summary(30, retailer)
        ranking_items = []
        
        if not store_df.empty:
            # Calculate total for percentage
            total_revenue = store_df["total_revenue"].sum()
            
            for i, (_, row) in enumerate(store_df.iterrows()):
                rank = i + 1
                medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
                pct = row["margin_pct"] if pd.notna(row["margin_pct"]) else 0
                revenue_share = (row["total_revenue"] / total_revenue * 100) if total_revenue > 0 else 0
                
                ranking_items.append(html.Div([
                    html.Div([
                        html.Span(medal, style={"fontSize": "20px", "width": "36px", "textAlign": "center"}),
                        html.Div([
                            html.Div(row["store_name"], style={"color": "#ddd", "fontSize": "13px", "fontWeight": "500"}),
                            html.Div(row["city"], style={"color": "#666", "fontSize": "11px"})
                        ], style={"flex": 1, "marginLeft": "12px"}),
                        html.Div([
                            html.Div(f"${row['total_revenue']:,.0f}", 
                                    style={"color": "#fff", "fontSize": "14px", "fontWeight": "600", "textAlign": "right"}),
                            html.Div([
                                html.Span(f"{pct:.1f}% margin", 
                                         style={"color": "#22c55e" if pct > 15 else "#f97316", "fontSize": "10px"}),
                                html.Span(f" • {revenue_share:.1f}% share", 
                                         style={"color": "#666", "fontSize": "10px", "marginLeft": "8px"})
                            ], style={"textAlign": "right"})
                        ])
                    ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
                    html.Div(style={
                        "width": f"{revenue_share}%",
                        "height": "2px",
                        "background": "linear-gradient(90deg, #00c853, #00ff66)",
                        "borderRadius": "2px",
                        "marginTop": "8px",
                        "transition": "width 0.3s ease"
                    })
                ], style={"padding": "12px 0", "borderBottom": "1px solid #1e1e1e"}))
        
        ranking_header = f"📊 Store Revenue Ranking — Last 30 Days ({retailer_name})"
        
        # Enhanced Alerts with icons and styling
        alerts = []
        
        if not inv.empty:
            critical = inv[inv["status"] == "CRITICAL"].head(6)
            for _, row in critical.iterrows():
                alerts.append(html.Div([
                    html.Div([
                        html.Span("🔴", style={"fontSize": "18px", "marginRight": "12px"}),
                        html.Div([
                            html.Div(f"{row['product_name'][:35]}", 
                                    style={"color": "#fff", "fontSize": "13px", "fontWeight": "500"}),
                            html.Div([
                                html.Span(f"{row['store_name']}", style={"color": "#888", "fontSize": "11px"}),
                                html.Span(f" • {row['current_stock']} units left", 
                                         style={"color": "#ef4444", "fontSize": "11px", "marginLeft": "8px"})
                            ])
                        ], style={"flex": 1})
                    ], style={"display": "flex", "alignItems": "flex-start"})
                ], style={"padding": "12px", "borderLeft": "3px solid #ef4444", 
                          "background": "rgba(239,68,68,0.05)", "borderRadius": "8px", "marginBottom": "8px"}))
        
        credit = get_supplier_credit()
        if not credit.empty:
            stopped = credit[credit["supplier_status"] == "STOPPED"]
            for _, row in stopped.head(3).iterrows():
                alerts.append(html.Div([
                    html.Div([
                        html.Span("⛔", style={"fontSize": "18px", "marginRight": "12px"}),
                        html.Div([
                            html.Div(f"{row['supplier_name']} — STOPPED", 
                                    style={"color": "#ef4444", "fontSize": "13px", "fontWeight": "500"}),
                            html.Div(f"${row['outstanding_usd']:,.0f} outstanding", 
                                    style={"color": "#888", "fontSize": "11px"})
                        ], style={"flex": 1})
                    ], style={"display": "flex", "alignItems": "center"})
                ], style={"padding": "12px", "borderLeft": "3px solid #ef4444", 
                          "background": "rgba(239,68,68,0.05)", "borderRadius": "8px", "marginBottom": "8px"}))
        
        if not alerts:
            alerts = [html.Div([
                html.Div("✅ No critical alerts", style={"color": "#22c55e", "fontSize": "14px"}),
                html.Div("All systems operating normally", style={"color": "#666", "fontSize": "12px", "marginTop": "4px"})
            ], style={"textAlign": "center", "padding": "40px"})]
        
        return kpi_cards, fig_trend, fig_cat, ranking_items, ranking_header, alerts
        
    except Exception as e:
        print(f"Error in overview: {e}")
        import traceback
        traceback.print_exc()
        
        empty_fig = go.Figure()
        empty_fig.update_layout(
            **CHART_LAYOUT,
            title={"text": f"⚠️ Error Loading Data", "font": {"color": "#ef4444", "size": 14}},
            annotations=[{
                "text": str(e)[:100],
                "showarrow": False,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "font": {"color": "#888", "size": 12}
            }]
        )
        
        error_message = html.Div([
            html.Div("⚠️ Error Loading Data", style={
                "fontSize": "18px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "12px"
            }),
            html.Div(str(e)[:150], style={"color": "#888", "fontSize": "13px"}),
            html.Div("Please check that the database contains the required data.", 
                    style={"color": "#666", "fontSize": "12px", "marginTop": "12px"})
        ], style={"textAlign": "center", "padding": "40px"})
        
        return [], empty_fig, empty_fig, [], f"Store Revenue Ranking — Last 30 Days ({retailer_name})", error_message
