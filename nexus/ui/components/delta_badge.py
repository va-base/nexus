"""Delta badge component for displaying belief changes"""
import streamlit as st


def render_delta_badge(prior: float, posterior: float, show_percentage: bool = True):
    """
    Render a delta badge showing belief change
    
    Args:
        prior: Prior belief value
        posterior: Posterior belief value
        show_percentage: Whether to show percentage change
    """
    delta = posterior - prior
    delta_pct = delta * 100
    
    if delta > 0:
        color = "#10b981"  # green
        arrow = "↑"
    elif delta < 0:
        color = "#ef4444"  # red
        arrow = "↓"
    else:
        color = "#6b7280"  # gray
        arrow = "→"
    
    if show_percentage:
        st.markdown(
            f'<span style="color: {color}; font-weight: bold; font-size: 1.1em;">'
            f'{arrow} {abs(delta_pct):.2f}%</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<span style="color: {color}; font-weight: bold; font-size: 1.1em;">'
            f'{arrow} {abs(delta):.3f}</span>',
            unsafe_allow_html=True
        )
