"""Customer Sentiment — Page 13 with Retailer Filter & Store Performance Correlation"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/sentiment", name="Customer Sentiment", order=12)

def get_sentiment_data(retailer=None):
    """Generate synthetic sentiment data from stores"""
    try:
        stores = get_stores(retailer)
        
        if stores.empty:
            print(f"Warning: No stores found for sentiment data - {retailer}")
            return pd.DataFrame()
        
        np.random.seed(77)
        complaint_categories = ["Empty Shelves", "Long Queues", "Poor Service", "Pricing",
                                 "Product Quality", "Cleanliness", "Parking", "Opening Hours"]
        records = []
        months = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='ME').strftime("%Y-%m").tolist()
        
        for _, s in stores.iterrows():
            base_nps = np.random.randint(28, 72)
            for month in months:
                nps_variation = base_nps + np.random.randint(-8, 8)
                for cat in complaint_categories:
                    records.append({
                        "store_id": s["store_id"], 
                        "store_name": s["name"], 
                        "city": s["city"],
                        "retailer_id": s["retailer_id"],
                        "month": month, 
                        "nps_score": max(0, min(100, nps_variation)),
                        "complaint_category": cat, 
                        "complaint_count": np.random.randint(2, 45)
                    })
        return pd.DataFrame(records)
    except Exception as e:
        print(f"Error generating sentiment data: {e}")
        return pd.DataFrame()


def layout():
    return html.Div([
        page_header("Customer Sentiment", "NPS scores, complaint trends and satisfaction by store", "fa-face-smile"),
        html.Div(id="sentiment-content", style={"padding": "20px 28px"})
    ])


@callback(
    Output("sentiment-content", "children"),
    Input("active-retailer", "data")
)
def update_sentiment(retailer):
    try:
        df = get_sentiment_data(retailer)
        
        retailer_name = retailer if retailer != "ALL" else "All Retailers"
        
        if df.empty:
            return html.Div([
                html.Div(f"No sentiment data available for {retailer_name}", 
                        style={"textAlign": "center", "padding": "60px", "color": "#888"})
            ])

        # Get store performance data for correlation
        store_performance = get_store_revenue_summary(30, retailer)
        
        # Merge sentiment with performance data
        if not store_performance.empty:
            store_perf_dict = store_performance.set_index("store_name")["total_revenue"].to_dict()
            store_margin_dict = store_performance.set_index("store_name")["margin_pct"].to_dict()
            df["revenue"] = df["store_name"].map(store_perf_dict).fillna(0)
            df["margin_pct"] = df["store_name"].map(store_margin_dict).fillna(0)

        # Calculate KPIs
        store_avg_nps = df.groupby("store_name")["nps_score"].mean()
        national_nps = store_avg_nps.mean()
        best_store = store_avg_nps.idxmax() if not store_avg_nps.empty else "N/A"
        worst_store = store_avg_nps.idxmin() if not store_avg_nps.empty else "N/A"
        total_complaints = df["complaint_count"].sum()
        nps_color = "#22c55e" if national_nps > 60 else "#eab308" if national_nps > 40 else "#ef4444"

        # Calculate correlation between NPS and revenue
        if not df.empty and "revenue" in df.columns:
            nps_rev_corr = df.groupby("store_name")[["nps_score", "revenue"]].mean().corr().iloc[0, 1]
        else:
            nps_rev_corr = 0
        correlation_color = "#22c55e" if nps_rev_corr > 0.3 else "#ef4444" if nps_rev_corr < -0.3 else "#eab308"

        kpis = [
            kpi_card("National NPS", f"{national_nps:.0f}", None, None, "fa-star", nps_color),
            kpi_card("Best Store", best_store[:16], None, None, "fa-trophy", "#22c55e"),
            kpi_card("Needs Attention", worst_store[:16], None, None, "fa-circle-exclamation", "#ef4444"),
            kpi_card("Total Complaints", f"{total_complaints:,}", None, None, "fa-comment-dots", "#f97316"),
            kpi_card("NPS × Revenue Corr", f"{nps_rev_corr:.2f}", None, None, "fa-chart-line", correlation_color),
        ]

        # NPS by store with revenue overlay
        nps_by_store = df.groupby("store_name")["nps_score"].mean().sort_values(ascending=True).reset_index()
        nps_colors = ["#22c55e" if n > 60 else "#eab308" if n > 40 else "#ef4444" for n in nps_by_store["nps_score"]]
        
        fig_nps = go.Figure()
        fig_nps.add_trace(go.Bar(
            x=nps_by_store["nps_score"].round(0), y=nps_by_store["store_name"],
            orientation="h", marker_color=nps_colors,
            name="NPS Score",
            text=nps_by_store["nps_score"].apply(lambda x: f"{x:.0f}"), textposition="outside"
        ))
        
        # Add revenue markers if available
        if "revenue" in df.columns and not df.empty and df["revenue"].sum() > 0:
            store_rev = df.groupby("store_name")["revenue"].mean().reset_index()
            fig_nps.add_trace(go.Scatter(
                x=store_rev["revenue"] / 1000, y=store_rev["store_name"],
                mode="markers", marker=dict(symbol="diamond", size=10, color="#00c853"),
                name="Revenue ($K)", xaxis="x2"
            ))
        
        fig_nps.add_vline(x=60, line_dash="dash", line_color="#22c55e")
        fig_nps.add_vline(x=40, line_dash="dash", line_color="#eab308")
        
        # Update layout with secondary x-axis for revenue
        fig_nps.update_layout(
            **CHART_LAYOUT,
            title={"text": f"NPS Score by Store (Diamonds = Revenue $K) - {retailer_name}", "font": {"color": "#ccc", "size": 13}},
            xaxis_range=[0, 110],
            height=400,
            xaxis2=dict(
                title="Revenue ($K)",
                overlaying="x",
                side="top",
                showgrid=False,
                titlefont=dict(color="#00c853")
            )
        )
        fig_nps.update_xaxes(tickangle=0)

        # Complaints pie
        comp_totals = df.groupby("complaint_category")["complaint_count"].sum().sort_values(ascending=False).reset_index()
        fig_pie = go.Figure(go.Pie(
            labels=comp_totals["complaint_category"], values=comp_totals["complaint_count"], hole=0.4,
            marker={"colors": ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#06b6d4", "#ec4899"]}
        ))
        fig_pie.update_layout(**CHART_LAYOUT, title={"text": f"Complaint Categories - {retailer_name}", "font": {"color": "#ccc", "size": 13}})

        # NPS trend
        nps_trend = df.groupby("month")["nps_score"].mean().reset_index()
        fig_trend = go.Figure(go.Scatter(
            x=nps_trend["month"], y=nps_trend["nps_score"],
            mode="lines+markers", line={"color": "#3b82f6", "width": 2},
            marker={"size": 7, "color": "#3b82f6"},
            fill="tozeroy", fillcolor="rgba(59,130,246,0.08)"
        ))
        fig_trend.add_hline(y=60, line_dash="dash", line_color="#22c55e")
        fig_trend.add_hline(y=40, line_dash="dash", line_color="#ef4444")
        fig_trend.update_layout(**CHART_LAYOUT, title={"text": f"National NPS Trend - {retailer_name}", "font": {"color": "#ccc", "size": 13}},
                                 yaxis_range=[0, 100])

        # Complaint vs Revenue correlation scatter plot
        complaint_by_store = df.groupby("store_name")[["complaint_count", "revenue", "margin_pct"]].sum().reset_index()
        if not complaint_by_store.empty and complaint_by_store["revenue"].sum() > 0:
            fig_corr = px.scatter(
                complaint_by_store, x="complaint_count", y="revenue",
                size="margin_pct", color="margin_pct",
                text="store_name",
                color_continuous_scale=["#ef4444", "#eab308", "#22c55e"],
                title=f"Complaints vs Revenue (Bubble size = Margin %) - {retailer_name}"
            )
            fig_corr.update_layout(**CHART_LAYOUT)
            fig_corr.update_traces(textposition="top center", textfont={"size": 10})
        else:
            fig_corr = go.Figure()
            fig_corr.update_layout(**CHART_LAYOUT, title={"text": "No correlation data available"})

        # Complaint heatmap
        pivot = df.groupby(["store_name", "complaint_category"])["complaint_count"].sum().unstack(fill_value=0)
        pivot.index = [n[:16] for n in pivot.index]
        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
            colorscale=[[0, "#0d0d0d"], [0.5, "#f97316"], [1, "#ef4444"]], showscale=True
        ))
        fig_hm.update_layout(**CHART_LAYOUT, title={"text": f"Store × Complaint Heatmap (Red = High Complaints) - {retailer_name}", "font": {"color": "#ccc", "size": 13}})
        fig_hm.update_xaxes(tickangle=-30)

        return html.Div([
            html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                     style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_nps, config={"displayModeBar": False})],
                         style={"flex": "1.5", "background": "#161616", "border": "1px solid #222", 
                                "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_pie, config={"displayModeBar": False})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", 
                                "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px", "flexWrap": "wrap"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_trend, config={"displayModeBar": False})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", 
                                "borderRadius": "10px", "padding": "16px"}),
                html.Div([dcc.Graph(figure=fig_corr, config={"displayModeBar": False})],
                         style={"flex": "1", "background": "#161616", "border": "1px solid #222", 
                                "borderRadius": "10px", "padding": "16px"}),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "14px", "flexWrap": "wrap"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_hm, config={"displayModeBar": False})],
                         style={"background": "#161616", "border": "1px solid #222", 
                                "borderRadius": "10px", "padding": "16px"})
            ]),
        ])
        
    except Exception as e:
        print(f"Error in sentiment layout: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.Div("⚠️ Error Loading Data", style={
                "fontSize": "20px", "fontWeight": "700", "color": "#ef4444", "marginBottom": "16px"
            }),
            html.Div(str(e), style={"color": "#888", "fontSize": "14px"}),
            html.Div(f"Please check that the database contains store data for {retailer}.",
                    style={"color": "#666", "fontSize": "12px", "marginTop": "12px"})
        ], style={"textAlign": "center", "padding": "60px"})
