"""Claim table component for displaying claims"""
import streamlit as st
import pandas as pd


def render_claim_table(claims: list, show_relevance: bool = False):
    """
    Render a table of claims
    
    Args:
        claims: List of claim dictionaries
        show_relevance: Whether to show relevance scores (for hypothesis-linked claims)
    """
    if not claims:
        st.info("No claims found")
        return
    
    display_data = []
    for claim in claims:
        row = {
            "Claim": claim.get("claim_text", ""),
            "Type": claim.get("claim_type", "").title() if claim.get("claim_type") else "N/A",
            "Polarity": claim.get("polarity", "").title() if claim.get("polarity") else "N/A",
            "Magnitude": f"{claim.get('magnitude', 0):.2f}" if claim.get("magnitude") is not None else "N/A",
            "Confidence": f"{claim.get('confidence', 0):.2f}" if claim.get("confidence") is not None else "N/A"
        }
        
        if show_relevance and "relevance_score" in claim:
            row["Relevance"] = f"{claim.get('relevance_score', 0):.3f}"
            row["Impact"] = claim.get("impact_direction", "").title() if claim.get("impact_direction") else "N/A"
        
        display_data.append(row)
    
    df = pd.DataFrame(display_data)
    
    def style_polarity(val):
        if val == "Positive":
            return "background-color: #d1fae5; color: #065f46"
        elif val == "Negative":
            return "background-color: #fee2e2; color: #991b1b"
        else:
            return "background-color: #f3f4f6; color: #374151"
    
    def style_impact(val):
        if val == "Supports":
            return "background-color: #d1fae5; color: #065f46"
        elif val == "Contradicts":
            return "background-color: #fee2e2; color: #991b1b"
        else:
            return "background-color: #f3f4f6; color: #374151"
    
    styled_df = df.style.applymap(style_polarity, subset=["Polarity"])
    
    if show_relevance and "Impact" in df.columns:
        styled_df = styled_df.applymap(style_impact, subset=["Impact"])
    
    st.dataframe(styled_df, use_container_width=True, height=400)
