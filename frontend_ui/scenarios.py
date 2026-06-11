import streamlit as st
from data_intelligence.quant_engine import QuantInsightEngine

def render_goal_1_scenarios(df, trace):
    """Interactive What-If for Goal 1: Price Reach Simulator"""
    st.markdown("#### 🎛️ Price Reach Simulator")
    st.write("Adjust the target price to see projected market reach.")
    
    price_points = df['willingness_to_pay_inr'].dropna()
    if price_points.empty:
        st.warning("Missing WTP data.")
        return
        
    min_p, max_p = int(price_points.min()), int(price_points.max())
    p50 = int(price_points.median())
    
    price = st.slider("Target Price (₹)", min_value=min_p, max_value=max_p, value=p50, step=10)
    reach = QuantInsightEngine.reach_at_price(df, price)
    
    st.success(f"**At ₹{price}, you can reach {reach:.1f}% of the surveyed market.**")

def render_goal_6_scenarios(df, trace):
    """Interactive What-If for Goal 6: RICE Simulator"""
    st.markdown("#### 🎛️ RICE Re-calculator")
    st.write("Test out alternative estimations to see how they impact RICE scores.")
    
    col1, col2 = st.columns(2)
    with col1:
        reach = st.slider("Reach", min_value=100, max_value=10000, value=5000, step=100)
        impact = st.slider("Impact (1-3)", min_value=1.0, max_value=3.0, value=2.0, step=0.5)
    with col2:
        conf = st.slider("Confidence (%)", min_value=50, max_value=100, value=80, step=5)
        effort = st.slider("Effort (months)", min_value=1.0, max_value=12.0, value=3.0, step=0.5)
        
    score = QuantInsightEngine.rice_at(reach, impact, conf, effort)
    st.success(f"**Projected RICE Score:** {score:.1f}")

def render_scenarios_for_goal(goal_key, df, trace):
    if goal_key == "GOAL_1_LAUNCH":
        render_goal_1_scenarios(df, trace)
    elif goal_key == "GOAL_6_ROADMAP":
        render_goal_6_scenarios(df, trace)
