"""
Shared UI components used across all pages
"""
from dash import html
import dash_bootstrap_components as dbc

# Enhanced Chart Layout with modern styling
CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#aaa", "family": "DM Sans, sans-serif", "size": 12},
    "xaxis": {
        "gridcolor": "#1e1e1e",
        "linecolor": "#2a2a2a",
        "tickcolor": "#444",
        "showgrid": True,
        "gridwidth": 0.5,
        "zerolinecolor": "#2a2a2a",
        "zerolinewidth": 1
    },
    "yaxis": {
        "gridcolor": "#1e1e1e",
        "linecolor": "#2a2a2a",
        "tickcolor": "#444",
        "showgrid": True,
        "gridwidth": 0.5,
        "zerolinecolor": "#2a2a2a"
    },
    "margin": {"t": 50, "b": 50, "l": 60, "r": 30},
    "legend": {
        "bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#aaa"},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1
    },
    "hovermode": "x unified",
    "hoverlabel": {
        "bgcolor": "#1a1a1a",
        "font": {"color": "#fff", "size": 12},
        "bordercolor": "#00c853"
    },
    "colorway": ["#00c853", "#3b82f6", "#f97316", "#8b5cf6", "#06b6d4", "#eab308", "#ec4899", "#14b8a6", "#f59e0b"],
    "transition": {"duration": 500, "easing": "cubic-in-out"}
}


def page_header(title, subtitle=None, icon=None):
    """Enhanced page header with animation"""
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"fa-solid {icon}",
                       style={
                           "fontSize": "24px",
                           "color": "#00c853",
                           "marginRight": "12px",
                           "background": "linear-gradient(135deg, #00c853, #00ff66)",
                           "WebkitBackgroundClip": "text",
                           "WebkitTextFillColor": "transparent",
                           "backgroundClip": "text"
                       }) if icon else None,
                html.Div([
                    html.H2(title, style={
                        "margin": 0,
                        "color": "#fff",
                        "fontFamily": "'Syne', sans-serif",
                        "fontWeight": "700",
                        "fontSize": "24px",
                        "letterSpacing": "-0.5px",
                        "background": "linear-gradient(135deg, #fff, #ccc)",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "backgroundClip": "text"
                    }),
                    html.P(subtitle, style={
                        "margin": "4px 0 0",
                        "color": "#888",
                        "fontSize": "13px"
                    }) if subtitle else None
                ])
            ], style={"display": "flex", "alignItems": "center"})
        ])
    ], style={"padding": "24px 28px 16px", "borderBottom": "1px solid #1e1e1e"})


def kpi_card(title, value, delta=None, delta_label=None, icon=None,
             color="#00c853", bg="#161616"):
    """Enhanced KPI card with gradient and hover effect"""
    delta_color = "#22c55e" if (delta and delta >= 0) else "#ef4444"
    delta_arrow = "▲" if (delta and delta >= 0) else "▼"
    
    # Determine border gradient based on value trend
    border_gradient = f"linear-gradient(135deg, {color}, {color}80)"
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=f"fa-solid {icon}",
                       style={
                           "fontSize": "18px",
                           "color": color,
                           "background": f"radial-gradient(circle at 30% 30%, {color}20, transparent)",
                           "padding": "8px",
                           "borderRadius": "10px"
                       })
            ], style={
                "width": "40px",
                "height": "40px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "background": f"{color}10",
                "borderRadius": "12px"
            }) if icon else None,
            html.Div([
                html.Div(title, style={
                    "color": "#888",
                    "fontSize": "11px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.8px",
                    "fontWeight": "500"
                }),
                html.Div(value, style={
                    "color": "#fff",
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "fontFamily": "'Syne', sans-serif",
                    "lineHeight": "1.1",
                    "marginTop": "4px",
                    "letterSpacing": "-0.5px"
                }),
                html.Div([
                    html.Span(f"{delta_arrow} {abs(delta):.1f}%",
                              style={"color": delta_color, "fontSize": "12px", "fontWeight": "600"}),
                    html.Span(f" {delta_label}",
                              style={"color": "#666", "fontSize": "11px"})
                ]) if delta is not None else None
            ], style={"flex": 1, "marginLeft": "12px" if icon else 0})
        ], style={"display": "flex", "alignItems": "center"})
    ], style={
        "background": bg,
        "border": f"1px solid {color}20",
        "borderRadius": "16px",
        "padding": "18px 20px",
        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "cursor": "pointer",
        "position": "relative",
        "overflow": "hidden"
    }, className="kpi-card")


def status_badge(status):
    """Enhanced status badge with gradient effects"""
    colors = {
        "CRITICAL": ("#ef4444", "#2d0a0a", "linear-gradient(135deg, #ef4444, #dc2626)"),
        "LOW": ("#f97316", "#2d1500", "linear-gradient(135deg, #f97316, #ea580c)"),
        "ADEQUATE": ("#eab308", "#2d2500", "linear-gradient(135deg, #eab308, #ca8a04)"),
        "GOOD": ("#22c55e", "#0a2d15", "linear-gradient(135deg, #22c55e, #16a34a)"),
        "ACTIVE": ("#22c55e", "#0a2d15", "linear-gradient(135deg, #22c55e, #16a34a)"),
        "LIMITED_CREDIT": ("#f97316", "#2d1500", "linear-gradient(135deg, #f97316, #ea580c)"),
        "STOPPED": ("#ef4444", "#2d0a0a", "linear-gradient(135deg, #ef4444, #dc2626)"),
        "DELIVERED": ("#22c55e", "#0a2d15", "linear-gradient(135deg, #22c55e, #16a34a)"),
        "IN_TRANSIT": ("#3b82f6", "#0a1a2d", "linear-gradient(135deg, #3b82f6, #2563eb)"),
        "DELAYED": ("#ef4444", "#2d0a0a", "linear-gradient(135deg, #ef4444, #dc2626)"),
        "DISPATCHED": ("#8b5cf6", "#1a0a2d", "linear-gradient(135deg, #8b5cf6, #7c3aed)"),
        "ORDER_PLACED": ("#6b7280", "#1a1a1a", "linear-gradient(135deg, #6b7280, #4b5563)"),
        "AT_WAREHOUSE": ("#06b6d4", "#0a2530", "linear-gradient(135deg, #06b6d4, #0891b2)"),
    }
    fg, bg, gradient = colors.get(status, ("#888", "#1a1a1a", "linear-gradient(135deg, #888, #666)"))
    return html.Span(status.replace("_", " "), style={
        "background": gradient,
        "color": "white",
        "border": "none",
        "borderRadius": "20px",
        "padding": "2px 12px",
        "fontSize": "11px",
        "fontWeight": "600",
        "letterSpacing": "0.3px",
        "display": "inline-block",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.2)"
    })


def section_card(title, children, style=None):
    """Enhanced section card with glassmorphism"""
    return html.Div([
        html.Div(title, style={
            "color": "#888",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "1px",
            "marginBottom": "14px",
            "fontWeight": "600",
            "display": "flex",
            "alignItems": "center",
            "gap": "8px"
        }),
        *children
    ], style={
        "background": "rgba(22, 22, 22, 0.8)",
        "backdropFilter": "blur(10px)",
        "border": "1px solid rgba(255,255,255,0.05)",
        "borderRadius": "16px",
        "padding": "20px",
        "transition": "all 0.3s ease",
        **(style or {})
    }, className="section-card")


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
