import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def load_inventory_data():
    from app.data_loader import load_table
    df = load_table("inventory")
    if df is None or df.empty:
        return pd.DataFrame()
    return df

def get_reorder_data():
    """Calculate reorder needs with proper shape handling"""
    inv = load_inventory_data()
    if inv.empty:
        return pd.DataFrame()
    
    # Reset index to avoid alignment issues
    inv = inv.reset_index(drop=True)
    
    # Extract columns safely
    current_stock = inv["current_stock"]
    reorder_point = inv["reorder_point"]
    
    # Convert to 1D arrays
    if isinstance(reorder_point, pd.DataFrame):
        # If reorder_point has multiple columns, take first
        reorder_point = reorder_point.iloc[:, 0]
    elif isinstance(reorder_point, pd.Series) and reorder_point.dtype == 'object':
        # If it contains arrays/list, extract first element
        reorder_point = reorder_point.apply(
            lambda x: x[0] if isinstance(x, (list, tuple, np.ndarray)) else x
        )
    
    # Ensure both are numeric
    current_stock = pd.to_numeric(current_stock, errors='coerce')
    reorder_point = pd.to_numeric(reorder_point, errors='coerce')
    
    # Fill NaN values
    current_stock = current_stock.fillna(0)
    reorder_point = reorder_point.fillna(0)
    
    # Now compare (both should be 1D)
    inv["reorder_needed"] = current_stock <= reorder_point
    
    return inv

def layout():
    st.subheader("🔄 Reorder Optimizer")
    
    try:
        inv = get_reorder_data()
        
        if inv.empty:
            st.warning("No inventory data available")
            return
        
        # Reorder summary
        reorder_count = inv["reorder_needed"].sum()
        total_products = len(inv)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Products Needing Reorder", reorder_count, 
                     delta=f"{reorder_count/total_products*100:.0f}%")
        with col2:
            st.metric("Total Products", total_products)
        with col3:
            reorder_value = inv[inv["reorder_needed"]]["reorder_cost"].sum() if "reorder_cost" in inv.columns else 0
            st.metric("Estimated Reorder Cost", f"${reorder_value:,.0f}")
        
        # Show reorder list
        if reorder_count > 0:
            st.subheader("📦 Items to Reorder")
            reorder_list = inv[inv["reorder_needed"]].copy()
            reorder_list = reorder_list.sort_values("current_stock", ascending=True)
            
            # Select relevant columns for display
            display_cols = ["product_name", "store_name", "current_stock", "reorder_point", "reorder_quantity"]
            available_cols = [col for col in display_cols if col in reorder_list.columns]
            st.dataframe(reorder_list[available_cols], use_container_width=True)
        else:
            st.success("✅ All inventory levels are healthy!")
        
        # Visualize reorder needs by store
        if "store_name" in inv.columns and inv["store_name"].notna().any():
            store_reorder = inv.groupby("store_name")["reorder_needed"].sum().reset_index()
            fig = px.bar(store_reorder, x="store_name", y="reorder_needed",
                         title="Reorder Needs by Store",
                         color="reorder_needed",
                         color_continuous_scale="Reds")
            fig.update_layout(xaxis_title="Store", yaxis_title="Items to Reorder")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.write("Debug info: Check data structure")
