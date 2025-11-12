"""Belief gauge component for displaying belief states"""
import streamlit as st
import plotly.graph_objects as go


def render_belief_gauge(belief: float, uncertainty: float = None, label: str = "Belief"):
    """
    Render a gauge chart for belief state
    
    Args:
        belief: Belief value between 0 and 1
        uncertainty: Optional uncertainty value
        label: Label for the gauge
    """
    if belief >= 0.7:
        color = "#10b981"  # green
    elif belief >= 0.5:
        color = "#3b82f6"  # blue
    elif belief >= 0.3:
        color = "#f59e0b"  # amber
    else:
        color = "#ef4444"  # red
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=belief,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': label, 'font': {'size': 16}},
        number={'suffix': "", 'font': {'size': 32}, 'valueformat': '.3f'},
        gauge={
            'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 0.3], 'color': '#fee2e2'},
                {'range': [0.3, 0.5], 'color': '#fef3c7'},
                {'range': [0.5, 0.7], 'color': '#dbeafe'},
                {'range': [0.7, 1], 'color': '#d1fae5'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 2},
                'thickness': 0.75,
                'value': belief
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'family': "Arial, sans-serif"}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if uncertainty is not None:
        st.caption(f"Uncertainty: ±{uncertainty:.3f}")
