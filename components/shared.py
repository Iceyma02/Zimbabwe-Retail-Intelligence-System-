"""
Shared UI components used across all pages
"""
from dash import html
import dash_bootstrap_components as dbc


def page_header(title, subtitle=None, icon=None):
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"fa-solid {icon}",
                       style={"fontSize": "22px", "color": "#00c853", "marginRight": "12px"})
                if icon else None,
                html.Div([
                    html.H2(title, style={
                        "margin": 0, "color": "#fff", "fontFamily": "'Syne', sans-serif",
                        "fontWeight": "700", "fontSize": "24px"
                    }),
                    html.P(subtitle, style={"margin": 0, "color": "#888", "fontSize": "13px"})
                    if subtitle else None
                ])
            ], style={"display": "flex", "alignItems": "center"})
        ])
    ], style={"padding": "24px 28px 16px", "borderBottom": "1px solid #1e1e1e"})


def kpi_card(title, value, delta=None, delta_label=None, icon=None,
             color="#00c853", bg="#161616"):
    delta_color = "#22c55e" if (delta and delta >= 0) else "#ef4444"
    delta_arrow = "▲" if (delta and delta >= 0) else "▼"

    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"fa-solid {icon}",
                       style={"fontSize": "16px", "color": color})
            ], style={
                "width": "38px", "height": "38px", "borderRadius": "8px",
                "background": f"{color}18", "display": "flex",
                "alignItems": "center", "justifyContent": "center"
            }) if icon else None,
            html.Div([
                html.Div(title, style={"color": "#888", "fontSize": "11px",
                                       "textTransform": "uppercase", "letterSpacing": "0.8px"}),
                html.Div(value, style={
                    "color": "#fff", "fontSize": "26px", "fontWeight": "700",
                    "fontFamily": "'Syne', sans-serif", "lineHeight": "1.1"
                }),
                html.Div([
                    html.Span(f"{delta_arrow} {abs(delta):.1f}%",
                              style={"color": delta_color, "fontSize": "12px", "fontWeight": "600"}),
                    html.Span(f" {delta_label}",
                              style={"color": "#666", "fontSize": "11px"})
                ]) if delta is not None else None
            ])
        ], style={"display": "flex", "alignItems": "center", "gap": "12px"})
    ], style={
        "background": bg, "border": "1px solid #222",
        "borderRadius": "10px", "padding": "18px 20px",
        "borderLeft": f"3px solid {color}"
    })


def status_badge(status):
    colors = {
        "CRITICAL": ("#ef4444", "#2d0a0a"),
        "LOW": ("#f97316", "#2d1500"),
        "ADEQUATE": ("#eab308", "#2d2500"),
        "GOOD": ("#22c55e", "#0a2d15"),
        "ACTIVE": ("#22c55e", "#0a2d15"),
        "LIMITED_CREDIT": ("#f97316", "#2d1500"),
        "STOPPED": ("#ef4444", "#2d0a0a"),
        "DELIVERED": ("#22c55e", "#0a2d15"),
        "IN_TRANSIT": ("#3b82f6", "#0a1a2d"),
        "DELAYED": ("#ef4444", "#2d0a0a"),
        "DISPATCHED": ("#8b5cf6", "#1a0a2d"),
        "ORDER_PLACED": ("#6b7280", "#1a1a1a"),
        "AT_WAREHOUSE": ("#06b6d4", "#0a2530"),
    }
    fg, bg = colors.get(status, ("#888", "#1a1a1a"))
    return html.Span(status.replace("_", " "), style={
        "background": bg, "color": fg, "border": f"1px solid {fg}30",
        "borderRadius": "4px", "padding": "2px 8px",
        "fontSize": "11px", "fontWeight": "600", "letterSpacing": "0.5px"
    })


def section_card(title, children, style=None):
    return html.Div([
        html.Div(title, style={
            "color": "#888", "fontSize": "11px", "textTransform": "uppercase",
            "letterSpacing": "1px", "marginBottom": "14px", "fontWeight": "600"
        }),
        *children
    ], style={
        "background": "#161616", "border": "1px solid #222",
        "borderRadius": "10px", "padding": "20px",
        **(style or {})
    })


CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#aaa", "family": "DM Sans, sans-serif", "size": 12},
    "xaxis": {"gridcolor": "#1e1e1e", "linecolor": "#2a2a2a", "tickcolor": "#444"},
    "yaxis": {"gridcolor": "#1e1e1e", "linecolor": "#2a2a2a", "tickcolor": "#444"},
    "margin": {"t": 30, "b": 40, "l": 50, "r": 20},
    "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#aaa"}},
    "colorway": ["#00c853", "#3b82f6", "#22c55e", "#f97316", "#8b5cf6",
                 "#06b6d4", "#eab308", "#ec4899", "#14b8a6", "#f59e0b"]
}

BRAND_GREEN = "#00c853"
COLORS = {
    "critical": "#ef4444",
    "warning": "#f97316",
    "caution": "#eab308",
    "good": "#22c55e",
    "info": "#3b82f6",
    "purple": "#8b5cf6",
    "cyan": "#06b6d4"
}
