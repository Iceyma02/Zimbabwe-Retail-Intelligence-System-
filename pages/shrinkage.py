import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def load_shrinkage_data():
    """Load shrinkage data from database"""
    from app.data_loader import load_table
    df = load_table("shrinkage")
    if df is None or df.empty:
        return pd.DataFrame()
    return df

def clean_column(col):
    """Clean problematic column values"""
    if col is None:
        return None
    if isinstance(col, (list, tuple, np.ndarray)):
        return col[0] if len(col) > 0 else None
    return col

def layout():
    st.subheader("📉 Stock Shrinkage Analysis")
    
    df = load_shrinkage_data()
    if df.empty:
        st.warning("No shrinkage data available")
        return
    
    # Reset index and clean data
    df = df.reset_index(drop=True)
    
    # Clean store_name column if it contains arrays
    if "store_name" in df.columns:
        df["store_name"] = df["store_name"].apply(clean_column)
    
    # Group by store
    try:
        store_totals = df.groupby("store_name", as_index=False)["value_usd"].sum()
        store_totals = store_totals.sort_values("value_usd", ascending=False)
        
        fig = px.bar(store_totals, x="store_name", y="value_usd",
                     title="Shrinkage by Store (USD)",
                     color="value_usd",
                     color_continuous_scale="Reds")
        fig.update_layout(xaxis_title="Store", yaxis_title="Shrinkage (USD)")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing shrinkage data: {e}")
        st.write("Data sample:", df.head())
    
    # Shrinkage by category
    if "category" in df.columns:
        df["category"] = df["category"].apply(clean_column)
        cat_totals = df.groupby("category", as_index=False)["value_usd"].sum()
        cat_totals = cat_totals.sort_values("value_usd", ascending=False)
        
        fig = px.pie(cat_totals, values="value_usd", names="category",
                     title="Shrinkage by Category")
        st.plotly_chart(fig, use_container_width=True)
