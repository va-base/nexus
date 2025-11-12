"""Evidence card component for displaying evidence items"""
import streamlit as st
from datetime import datetime


def render_evidence_card(evidence: dict, show_content: bool = False):
    """
    Render an evidence card
    
    Args:
        evidence: Evidence dictionary with id, title, source_type, source_date, validation_status
        show_content: Whether to show content preview
    """
    status_colors = {
        "validated": "#10b981",
        "pending": "#f59e0b",
        "rejected": "#ef4444",
        "mnpi_hold": "#8b5cf6"
    }
    
    status = evidence.get("validation_status", "pending")
    status_color = status_colors.get(status, "#6b7280")
    
    source_colors = {
        "filing": "#3b82f6",
        "transcript": "#8b5cf6",
        "hiring": "#10b981",
        "news": "#f59e0b",
        "manual": "#6b7280"
    }
    
    source_type = evidence.get("source_type", "manual")
    source_color = source_colors.get(source_type, "#6b7280")
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{evidence.get('title', 'Untitled')}**")
        
        with col2:
            st.markdown(
                f'<span style="background-color: {source_color}; color: white; '
                f'padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">'
                f'{source_type.upper()}</span>',
                unsafe_allow_html=True
            )
        
        col3, col4 = st.columns([3, 1])
        
        with col3:
            source_date = evidence.get("source_date", "")
            if source_date:
                st.caption(f"📅 {source_date}")
        
        with col4:
            st.markdown(
                f'<span style="background-color: {status_color}; color: white; '
                f'padding: 2px 8px; border-radius: 4px; font-size: 0.75em;">'
                f'{status.upper()}</span>',
                unsafe_allow_html=True
            )
        
        if show_content and "content" in evidence:
            with st.expander("Preview"):
                st.text(evidence["content"][:500] + "..." if len(evidence.get("content", "")) > 500 else evidence.get("content", ""))
        
        st.divider()
