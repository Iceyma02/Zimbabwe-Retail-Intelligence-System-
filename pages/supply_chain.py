"""Supply Chain Pipeline — Page 9"""
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.db import *
from components.shared import *

dash.register_page(__name__, path="/supply-chain", name="Supply Chain", order=8)

PIPELINE_STAGES = ["ORDER_PLACED","DISPATCHED","IN_TRANSIT","AT_WAREHOUSE","DELIVERED"]

def layout():
    return html.Div([
        page_header("Supply Chain Pipeline", "End-to-end visibility from supplier factory to store shelf", "fa-truck-fast"),
        html.Div([
            html.Div(id="sc-pipeline-flow", style={"marginBottom":"20px"}),
            html.Div([
                html.Div([
                    dcc.Graph(id="sc-status-chart", config={"displayModeBar":False}, style={"height":"260px"})
                ], style={"flex":1,"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"16px"}),
                html.Div([
                    dcc.Graph(id="sc-value-chart", config={"displayModeBar":False}, style={"height":"260px"})
                ], style={"flex":1,"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"16px"}),
            ], style={"display":"flex","gap":"14px","marginBottom":"14px"}),
            html.Div([
                html.Div("Active Orders", style={"color":"#888","fontSize":"11px","textTransform":"uppercase",
                                                  "letterSpacing":"1px","marginBottom":"14px"}),
                html.Div(id="sc-orders-table")
            ], style={"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"20px"}),
            dcc.Interval(id="sc-load", interval=99999999, n_intervals=0, max_intervals=1)
        ], style={"padding":"20px 28px"})
    ])

@callback(
    Output("sc-pipeline-flow","children"),
    Output("sc-status-chart","figure"),
    Output("sc-value-chart","figure"),
    Output("sc-orders-table","children"),
    Input("sc-load","n_intervals")
)
def update_sc(_):
    df = get_logistics()
    status_counts = df["status"].value_counts().to_dict()
    delayed = df[df["status"]=="DELAYED"]
    in_transit_val = df[df["status"]=="IN_TRANSIT"]["order_value_usd"].sum()

    # Pipeline flow visual
    stage_colors = {
        "ORDER_PLACED":"#6b7280","DISPATCHED":"#8b5cf6","IN_TRANSIT":"#3b82f6",
        "AT_WAREHOUSE":"#06b6d4","DELIVERED":"#22c55e","DELAYED":"#ef4444"
    }
    pipeline_nodes = []
    for stage in PIPELINE_STAGES:
        count = status_counts.get(stage, 0)
        color = stage_colors[stage]
        pipeline_nodes.append(html.Div([
            html.Div(str(count), style={"fontSize":"28px","fontWeight":"800","color":color,
                                         "fontFamily":"'Syne', sans-serif"}),
            html.Div(stage.replace("_"," "), style={"color":"#888","fontSize":"11px","letterSpacing":"0.5px"}),
            html.Div(style={"width":"100%","height":"3px","background":color,"borderRadius":"2px","marginTop":"8px"})
        ], style={"flex":1,"background":"#161616","border":f"1px solid {color}40","borderRadius":"10px",
                  "padding":"16px 12px","textAlign":"center"}))

        if stage != PIPELINE_STAGES[-1]:
            pipeline_nodes.append(html.Div("→", style={"color":"#444","fontSize":"20px",
                                                         "display":"flex","alignItems":"center","padding":"0 4px"}))

    # Delayed badge
    delayed_badge = html.Div([
        html.Span("⚠️ ", style={"fontSize":"14px"}),
        html.Span(f"{len(delayed)} DELAYED orders", style={"color":"#ef4444","fontWeight":"600","fontSize":"13px"}),
        html.Span(f" — Total value: ${df[df['status']=='DELAYED']['order_value_usd'].sum():,.0f}",
                  style={"color":"#888","fontSize":"12px"})
    ], style={"background":"#2d0a0a","border":"1px solid #ef444440","borderRadius":"8px",
              "padding":"10px 16px","marginTop":"12px"}) if len(delayed) > 0 else html.Div()

    pipeline = html.Div([
        html.Div(pipeline_nodes, style={"display":"flex","alignItems":"stretch","gap":"4px"}),
        delayed_badge
    ], style={"background":"#161616","border":"1px solid #222","borderRadius":"10px","padding":"20px"})

    # Status donut
    status_df = df["status"].value_counts().reset_index()
    status_df.columns = ["status","count"]
    fig_status = go.Figure(go.Pie(
        labels=status_df["status"], values=status_df["count"], hole=0.45,
        marker={"colors":[stage_colors.get(s,"#888") for s in status_df["status"]]}
    ))
    fig_status.update_layout(**CHART_LAYOUT, title={"text":"Order Status Distribution","font":{"color":"#ccc","size":13}})

    # Value by supplier
    sup_val = df.groupby("supplier_name")["order_value_usd"].sum().sort_values(ascending=False).head(10).reset_index()
    fig_val = go.Figure(go.Bar(
        x=sup_val["order_value_usd"], y=sup_val["supplier_name"],
        orientation="h", marker_color="#3b82f6"
    ))
    fig_val.update_layout(**CHART_LAYOUT, title={"text":"Order Value by Supplier (Top 10)","font":{"color":"#ccc","size":13}},
                           yaxis={"categoryorder":"total ascending"})

    # Orders table
    headers = ["Order ID","Supplier","Store","Value","Status","Expected","Delay"]
    header_row = html.Tr([html.Th(h, style={"color":"#666","fontSize":"11px","padding":"7px 10px",
                                             "borderBottom":"1px solid #2a2a2a","textTransform":"uppercase"}) for h in headers])
    rows = []
    for _, row in df.sort_values("order_value_usd", ascending=False).head(40).iterrows():
        rows.append(html.Tr([
            html.Td(row["order_id"], style={"color":"#3b82f6","padding":"6px 10px","fontSize":"12px"}),
            html.Td(row["supplier_name"], style={"color":"#ddd","padding":"6px 10px","fontSize":"12px"}),
            html.Td(row["store_name"], style={"color":"#888","padding":"6px 10px","fontSize":"11px"}),
            html.Td(f"${row['order_value_usd']:,.0f}", style={"color":"#22c55e","padding":"6px 10px"}),
            html.Td(status_badge(row["status"]), style={"padding":"6px 10px"}),
            html.Td(row["expected_delivery"], style={"color":"#aaa","padding":"6px 10px","fontSize":"11px"}),
            html.Td(f"{int(row['delay_days'])}d" if row["delay_days"] > 0 else "—",
                    style={"color":"#ef4444" if row["delay_days"] > 0 else "#444","padding":"6px 10px"}),
        ], style={"borderBottom":"1px solid #1a1a1a"}))

    table = html.Table([html.Thead(header_row), html.Tbody(rows)],
                       style={"width":"100%","borderCollapse":"collapse"})
    return pipeline, fig_status, fig_val, table
