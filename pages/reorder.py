"""Reorder Optimizer — Page 8"""
import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/reorder", name="Reorder Optimizer", order=7)

def get_reorder_data():
    inv = get_inventory_simple()
    sales_30 = get_sales(30)

    # Compute avg daily sales per product — result is a plain Series
    avg_daily = sales_30.groupby("product_id")["units_sold"].mean()

    # Map onto inventory using .map() — avoids alignment issues from merge
    inv = inv.copy()
    inv["avg_daily_sales"] = inv["product_id"].map(avg_daily).fillna(1.0)

    # Use .values to force numpy arrays — avoids pandas alignment errors
    inv["days_of_stock"] = (inv["current_stock"].values / inv["avg_daily_sales"].values).round(1)
    inv["reorder_needed"] = inv["current_stock"].values <= inv["reorder_point"].values

    needs = inv[inv["reorder_needed"]].copy()

    if needs.empty:
        return needs

    # Urgency score — use .values throughout to avoid index alignment issues
    days_vals = needs["days_of_stock"].values
    stock_vals = needs["current_stock"].values
    reorder_vals = needs["reorder_point"].values

    needs["urgency_score"] = (
        (1.0 / (days_vals + 0.1)) * 0.6 +
        (reorder_vals / (stock_vals + 1)) * 0.4
    )

    return needs.sort_values("urgency_score", ascending=False).reset_index(drop=True)


def layout():
    try:
        needs_reorder = get_reorder_data()

        total_need = len(needs_reorder)
        critical_need = len(needs_reorder[needs_reorder["days_of_stock"] < 3]) if total_need > 0 else 0
        total_order_value = float((needs_reorder["reorder_qty"] * needs_reorder["unit_cost"]).sum()) if total_need > 0 else 0

        kpis = [
            kpi_card("Items to Reorder", str(total_need), None, None, "fa-rotate", "#f97316"),
            kpi_card("Critical (<3 days)", str(critical_need), None, None, "fa-fire", "#ef4444"),
            kpi_card("Est. Order Value", f"${total_order_value:,.0f}", None, None, "fa-dollar-sign", "#3b82f6"),
        ]

        if total_need == 0:
            fig = go.Figure()
            fig.add_annotation(text="No items currently need reordering ✅",
                               xref="paper", yref="paper", x=0.5, y=0.5,
                               showarrow=False, font={"color": "#22c55e", "size": 16})
            fig.update_layout(**CHART_LAYOUT)
            table = html.Div("All stock levels are above reorder points.",
                             style={"color": "#22c55e", "padding": "20px"})
        else:
            top20 = needs_reorder.head(20)
            days_list = top20["days_of_stock"].tolist()
            fig = go.Figure(go.Bar(
                x=top20["urgency_score"].round(2).tolist(),
                y=top20["product_name"].str[:25].tolist(),
                orientation="h",
                marker_color=["#ef4444" if d < 3 else "#f97316" if d < 7 else "#eab308" for d in days_list]
            ))
            fig.update_layout(**CHART_LAYOUT,
                              title={"text": "Top 20 Items by Reorder Urgency Score",
                                     "font": {"color": "#ccc", "size": 13}},
                              yaxis={"categoryorder": "total ascending"})

            max_score = float(needs_reorder["urgency_score"].max()) or 1.0
            headers = ["Product", "Store", "Stock", "Days Left", "Reorder Qty", "Order Value", "Urgency"]
            header_row = html.Tr([
                html.Th(h, style={"color": "#666", "fontSize": "11px", "padding": "8px 10px",
                                   "borderBottom": "1px solid #2a2a2a", "textTransform": "uppercase"})
                for h in headers
            ])
            rows = []
            for _, row in needs_reorder.head(50).iterrows():
                days = float(row["days_of_stock"])
                score = float(row["urgency_score"])
                urgency_color = "#ef4444" if days < 3 else "#f97316" if days < 7 else "#eab308"
                order_val = float(row["reorder_qty"]) * float(row["unit_cost"])
                bar_width = min(score / max_score * 100, 100)
                rows.append(html.Tr([
                    html.Td(str(row["product_name"])[:28], style={"color": "#ddd", "padding": "7px 10px", "fontSize": "12px"}),
                    html.Td(str(row["store_name"]), style={"color": "#888", "padding": "7px 10px", "fontSize": "11px"}),
                    html.Td(str(int(row["current_stock"])), style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
                    html.Td(f"{days:.1f}d", style={"color": urgency_color, "padding": "7px 10px", "fontWeight": "600"}),
                    html.Td(str(int(row["reorder_qty"])), style={"color": "#3b82f6", "padding": "7px 10px"}),
                    html.Td(f"${order_val:,.0f}", style={"color": "#22c55e", "padding": "7px 10px"}),
                    html.Td(html.Div(style={
                        "width": f"{bar_width:.0f}%", "height": "6px",
                        "background": urgency_color, "borderRadius": "3px"
                    }), style={"padding": "7px 10px", "width": "80px"}),
                ], style={"borderBottom": "1px solid #1a1a1a"}))

            table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                               style={"width": "100%", "borderCollapse": "collapse"})

        return html.Div([
            page_header("Reorder Optimizer",
                        "Smart reorder suggestions based on stock levels, demand and supplier lead times",
                        "fa-rotate"),
            html.Div([
                html.Div([html.Div(k, style={"flex": 1}) for k in kpis],
                         style={"display": "flex", "gap": "14px", "marginBottom": "20px"}),
                html.Div([dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "280px"})],
                         style={"background": "#161616", "border": "1px solid #222",
                                "borderRadius": "10px", "padding": "16px", "marginBottom": "14px"}),
                html.Div([
                    html.Div("Reorder Queue — Prioritised by Urgency", style={
                        "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
                        "letterSpacing": "1px", "marginBottom": "14px"
                    }),
                    table
                ], style={"background": "#161616", "border": "1px solid #222",
                           "borderRadius": "10px", "padding": "20px"}),
            ], style={"padding": "20px 28px"})
        ])

    except Exception as e:
        import traceback
        return html.Div([
            page_header("Reorder Optimizer", "Error loading data", "fa-rotate"),
            html.Div([
                html.Div(f"⚠️ Error: {str(e)}", style={"color": "#ef4444", "padding": "20px"}),
                html.Pre(traceback.format_exc(), style={"color": "#888", "fontSize": "11px", "padding": "20px"})
            ])
        ])
