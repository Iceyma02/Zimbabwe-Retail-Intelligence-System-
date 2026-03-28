import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Define CHART_LAYOUT without yaxis to avoid duplication
CHART_LAYOUT = {
    "template": "plotly_white",
    "height": 500,
    "margin": dict(l=40, r=40, t=40, b=40)
}

def load_supplier_credit_data():
    from app.data_loader import load_table
    df = load_table("supplier_credit")
    if df is None or df.empty:
        return pd.DataFrame()
    return df

def layout():
    st.subheader("💳 Supplier Credit Management")
    
    df = load_supplier_credit_data()
    if df.empty:
        st.warning("No supplier credit data available")
        return
    
    df = df.reset_index(drop=True)
    
    # Credit status by supplier
    try:
        fig_status = go.Figure()
        
        # Add bars for credit balance
        fig_status.add_trace(go.Bar(
            x=df["supplier_name"],
            y=df["credit_balance"],
            name="Credit Balance",
            marker_color="#ff6b6b"
        ))
        
        # Add bars for payment terms
        fig_status.add_trace(go.Bar(
            x=df["supplier_name"],
            y=df["payment_terms_days"],
            name="Payment Terms (days)",
            marker_color="#4ecdc4",
            yaxis="y2"
        ))
        
        fig_status.update_layout(
            title="Supplier Credit Status",
            xaxis_title="Supplier",
            yaxis_title="Credit Balance (USD)",
            yaxis2=dict(
                title="Payment Terms (days)",
                overlaying="y",
                side="right"
            ),
            **CHART_LAYOUT  # This no longer contains yaxis
        )
        
        st.plotly_chart(fig_status, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating supplier credit chart: {e}")
    
    # Credit risk table
    df["risk_status"] = pd.cut(
        df["credit_balance"],
        bins=[-float('inf'), 5000, 20000, float('inf')],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    )
    
    st.subheader("📋 Credit Risk Summary")
    risk_summary = df.groupby("risk_status", as_index=False).agg({
        "supplier_name": "count",
        "credit_balance": "sum"
    }).rename(columns={"supplier_name": "supplier_count", "credit_balance": "total_credit"})
    
    st.dataframe(risk_summary, use_container_width=True)
