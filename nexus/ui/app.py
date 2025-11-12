"""Streamlit UI for Nexus - Enhanced Version"""
import streamlit as st
import requests
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from nexus.ui.components import render_belief_gauge, render_delta_badge, render_evidence_card, render_claim_table

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Nexus - Investment Research System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #334155;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_data(endpoint: str, params: dict = None):
    """Fetch data from API with caching"""
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def post_data(endpoint: str, data: dict):
    """Post data to API"""
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error posting data: {e}")
        return None

with st.sidebar:
    st.markdown("### 🔍 Nexus")
    st.markdown("Investment Research System")
    st.divider()
    
    page = st.selectbox(
        "Navigation",
        ["Dashboard", "Companies", "Themes", "Hypotheses", "Evidence", "Investigations", "Beliefs"]
    )
    
    st.divider()
    st.markdown("### ⚡ Quick Actions")
    
    with st.expander("➕ Add Hypothesis"):
        with st.form("quick_add_hypothesis"):
            hyp_statement = st.text_area("Statement", placeholder="Enter hypothesis statement...")
            hyp_type = st.selectbox("Type", ["growth", "margin", "market_share", "product", "risk"])
            hyp_belief = st.slider("Initial Belief", 0.0, 1.0, 0.5, 0.01)
            
            if st.form_submit_button("Create Hypothesis"):
                data = {
                    "statement": hyp_statement,
                    "hypothesis_type": hyp_type,
                    "initial_belief": hyp_belief
                }
                result = post_data("/api/hypotheses/", data)
                if result:
                    st.success("Hypothesis created!")
                    st.cache_data.clear()
    
    with st.expander("➕ Add Evidence"):
        with st.form("quick_add_evidence"):
            ev_title = st.text_input("Title")
            ev_source_type = st.selectbox("Source Type", ["filing", "transcript", "hiring", "news", "manual"])
            ev_content = st.text_area("Content", placeholder="Enter evidence content...")
            ev_url = st.text_input("Source URL (optional)")
            
            if st.form_submit_button("Submit Evidence"):
                data = {
                    "title": ev_title,
                    "source_type": ev_source_type,
                    "content": ev_content,
                    "source_url": ev_url if ev_url else None
                }
                result = post_data("/api/evidence/", data)
                if result:
                    st.success("Evidence submitted!")
                    st.cache_data.clear()

st.markdown('<h1 class="main-header">🔍 Nexus</h1>', unsafe_allow_html=True)

if page == "Dashboard":
    st.markdown("### Investment Research Dashboard")
    
    hypotheses_data = fetch_data("/api/hypotheses/", {"limit": 1000})
    evidence_data = fetch_data("/api/evidence/", {"limit": 1000})
    investigations_data = fetch_data("/api/investigations/", {"limit": 1000})
    recent_updates = fetch_data("/api/beliefs/updates/recent", {"limit": 10})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_hyp = len([h for h in (hypotheses_data or []) if h.get("status") == "active"])
        st.metric("Active Hypotheses", active_hyp)
    
    with col2:
        recent_evidence = len([e for e in (evidence_data or [])])
        st.metric("Total Evidence", recent_evidence)
    
    with col3:
        pending_inv = len([i for i in (investigations_data or []) if i.get("status") == "pending"])
        st.metric("Pending Investigations", pending_inv)
    
    with col4:
        recent_count = len(recent_updates or [])
        st.metric("Recent Updates", recent_count)
    
    st.divider()
    
    st.markdown('<h2 class="sub-header">Recent Belief Updates</h2>', unsafe_allow_html=True)
    
    if recent_updates:
        for update in recent_updates[:5]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{update.get('statement', 'Unknown')[:80]}...**")
                    st.caption(f"Updated: {update.get('created_at', 'Unknown')}")
                
                with col2:
                    render_delta_badge(update.get('prior_belief', 0), update.get('posterior_belief', 0))
                
                with col3:
                    st.metric("Belief", f"{update.get('posterior_belief', 0):.3f}")
                
                st.divider()
    else:
        st.info("No recent belief updates")
    
    st.markdown('<h2 class="sub-header">Belief Distribution</h2>', unsafe_allow_html=True)
    
    beliefs_data = fetch_data("/api/beliefs/current", {"limit": 1000})
    if beliefs_data:
        belief_values = [b.get("current_belief", 0.5) for b in beliefs_data]
        
        fig = px.histogram(
            x=belief_values,
            nbins=20,
            labels={"x": "Belief Value", "y": "Count"},
            title="Distribution of Current Beliefs"
        )
        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "Companies":
    st.markdown('<h2 class="sub-header">Companies</h2>', unsafe_allow_html=True)
    
    companies = fetch_data("/api/companies/", {"limit": 100})
    
    if companies:
        df = pd.DataFrame(companies)
        df = df[['ticker', 'name', 'sector', 'market_cap']].fillna("N/A")
        
        st.dataframe(df, use_container_width=True, height=400)
        
        st.divider()
        st.markdown("### Company Details")
        
        selected_company = st.selectbox(
            "Select a company",
            options=[c['id'] for c in companies],
            format_func=lambda x: next((f"{c['ticker']} - {c['name']}" for c in companies if c['id'] == x), "Unknown")
        )
        
        if selected_company:
            company_detail = fetch_data(f"/api/companies/{selected_company}")
            
            if company_detail:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Ticker:** {company_detail.get('ticker', 'N/A')}")
                    st.markdown(f"**Name:** {company_detail.get('name', 'N/A')}")
                    st.markdown(f"**Sector:** {company_detail.get('sector', 'N/A')}")
                
                with col2:
                    market_cap = company_detail.get('market_cap')
                    if market_cap:
                        st.markdown(f"**Market Cap:** ${market_cap:,}")
                    st.markdown(f"**Public:** {'Yes' if company_detail.get('is_public') else 'No'}")
                
                st.markdown("#### Active Hypotheses")
                company_hypotheses = fetch_data(f"/api/companies/{selected_company}/hypotheses")
                
                if company_hypotheses:
                    for hyp in company_hypotheses:
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{hyp.get('statement', 'Unknown')}**")
                                st.caption(f"Type: {hyp.get('hypothesis_type', 'N/A')}")
                            
                            with col2:
                                belief = hyp.get('current_belief')
                                if belief is not None:
                                    st.metric("Belief", f"{belief:.3f}")
                            
                            st.divider()
                else:
                    st.info("No active hypotheses for this company")
                
                st.markdown("#### Recent Evidence")
                company_evidence = fetch_data(f"/api/companies/{selected_company}/evidence", {"limit": 10})
                
                if company_evidence:
                    for ev in company_evidence[:5]:
                        render_evidence_card(ev)
                else:
                    st.info("No evidence for this company")
    else:
        st.info("No companies found")

elif page == "Themes":
    st.markdown('<h2 class="sub-header">Investment Themes</h2>', unsafe_allow_html=True)
    
    themes = fetch_data("/api/themes/", {"limit": 100})
    
    if themes:
        for theme in themes:
            with st.expander(f"📊 {theme.get('name', 'Unknown')}"):
                st.markdown(theme.get('description', 'No description'))
                
                theme_hypotheses = fetch_data(f"/api/themes/{theme['id']}/hypotheses")
                
                if theme_hypotheses:
                    st.markdown(f"**{len(theme_hypotheses)} Active Hypotheses**")
                    
                    for hyp in theme_hypotheses[:5]:
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.caption(hyp.get('statement', 'Unknown')[:80] + "...")
                        
                        with col2:
                            belief = hyp.get('current_belief')
                            if belief is not None:
                                st.caption(f"Belief: {belief:.3f}")
                else:
                    st.info("No hypotheses for this theme")
    else:
        st.info("No themes found")

elif page == "Hypotheses":
    st.markdown('<h2 class="sub-header">Hypotheses</h2>', unsafe_allow_html=True)
    
    hypotheses = fetch_data("/api/hypotheses/", {"limit": 100})
    
    if hypotheses:
        df = pd.DataFrame(hypotheses)
        df['current_belief'] = df['current_belief'].fillna(0.5).round(3)
        
        st.dataframe(
            df[['statement', 'hypothesis_type', 'current_belief', 'status']],
            use_container_width=True,
            height=400
        )
        
        st.divider()
        st.markdown("### Hypothesis Details")
        
        selected_id = st.selectbox(
            "Select hypothesis",
            options=[h['id'] for h in hypotheses],
            format_func=lambda x: next((h['statement'][:60] + "..." for h in hypotheses if h['id'] == x), "Unknown")
        )
        
        if selected_id:
            detail = fetch_data(f"/api/hypotheses/{selected_id}")
            
            if detail:
                st.markdown(f"**Statement:** {detail.get('statement', 'Unknown')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    belief = detail.get('current_belief', 0.5)
                    uncertainty = detail.get('uncertainty', 0)
                    render_belief_gauge(belief, uncertainty, "Current Belief")
                
                with col2:
                    st.markdown(f"**Type:** {detail.get('hypothesis_type', 'N/A')}")
                    st.markdown(f"**Status:** {detail.get('status', 'N/A')}")
                    st.markdown(f"**Created:** {detail.get('created_at', 'N/A')}")
                    st.markdown(f"**Last Updated:** {detail.get('last_updated', 'N/A')}")
                
                st.markdown("#### Belief History")
                history = fetch_data(f"/api/hypotheses/{selected_id}/history", {"limit": 50})
                
                if history:
                    history_df = pd.DataFrame(history)
                    history_df['created_at'] = pd.to_datetime(history_df['created_at'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=history_df['created_at'],
                        y=history_df['posterior_belief'],
                        mode='lines+markers',
                        name='Belief',
                        line=dict(color='#3b82f6', width=2)
                    ))
                    
                    fig.update_layout(
                        title="Belief Over Time",
                        xaxis_title="Date",
                        yaxis_title="Belief",
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No belief history")
                
                st.markdown("#### Contributing Claims")
                claims = fetch_data(f"/api/claims/hypothesis/{selected_id}", {"limit": 50})
                
                if claims:
                    render_claim_table(claims, show_relevance=True)
                else:
                    st.info("No claims linked to this hypothesis")
    else:
        st.info("No hypotheses found")

elif page == "Evidence":
    st.markdown('<h2 class="sub-header">Evidence</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_filter = st.selectbox("Filter by source type", ["All", "filing", "transcript", "hiring", "news", "manual"])
    
    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=200, value=50, step=10)
    
    params = {"limit": limit}
    if source_filter != "All":
        params["source_type"] = source_filter
    
    evidence = fetch_data("/api/evidence/", params)
    
    if evidence:
        st.markdown(f"**Showing {len(evidence)} evidence items**")
        
        for ev in evidence:
            render_evidence_card(ev, show_content=True)
            
            if st.button(f"View Claims", key=f"claims_{ev['id']}"):
                claims = fetch_data(f"/api/evidence/{ev['id']}/claims")
                if claims:
                    render_claim_table(claims)
                else:
                    st.info("No claims extracted yet")
    else:
        st.info("No evidence found")

elif page == "Investigations":
    st.markdown('<h2 class="sub-header">Investigations</h2>', unsafe_allow_html=True)
    
    status_filter = st.selectbox("Filter by status", ["All", "pending", "in_progress", "completed", "cancelled"])
    
    params = {"limit": 100}
    if status_filter != "All":
        params["status"] = status_filter
    
    investigations = fetch_data("/api/investigations/", params)
    
    if investigations:
        pending = [i for i in investigations if i.get('status') == 'pending']
        in_progress = [i for i in investigations if i.get('status') == 'in_progress']
        completed = [i for i in investigations if i.get('status') == 'completed']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📋 Pending")
            st.caption(f"{len(pending)} investigations")
            for inv in pending[:5]:
                with st.container():
                    st.markdown(f"**{inv.get('investigation_type', 'Unknown')}**")
                    st.caption(f"Priority: {inv.get('priority', 'N/A')}")
                    st.caption(f"Reason: {inv.get('trigger_reason', 'N/A')[:50]}...")
                    st.divider()
        
        with col2:
            st.markdown("### 🔄 In Progress")
            st.caption(f"{len(in_progress)} investigations")
            for inv in in_progress[:5]:
                with st.container():
                    st.markdown(f"**{inv.get('investigation_type', 'Unknown')}**")
                    st.caption(f"Priority: {inv.get('priority', 'N/A')}")
                    st.caption(f"Reason: {inv.get('trigger_reason', 'N/A')[:50]}...")
                    st.divider()
        
        with col3:
            st.markdown("### ✅ Completed")
            st.caption(f"{len(completed)} investigations")
            for inv in completed[:5]:
                with st.container():
                    st.markdown(f"**{inv.get('investigation_type', 'Unknown')}**")
                    st.caption(f"Priority: {inv.get('priority', 'N/A')}")
                    st.caption(f"Reason: {inv.get('trigger_reason', 'N/A')[:50]}...")
                    st.divider()
    else:
        st.info("No investigations found")

elif page == "Beliefs":
    st.markdown('<h2 class="sub-header">Current Beliefs</h2>', unsafe_allow_html=True)
    
    beliefs = fetch_data("/api/beliefs/current", {"limit": 200})
    
    if beliefs:
        df = pd.DataFrame(beliefs)
        df['current_belief'] = df['current_belief'].round(3)
        df['uncertainty'] = df['uncertainty'].fillna(0).round(3)
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            df[['statement', 'current_belief', 'uncertainty', 'last_updated']],
            use_container_width=True,
            height=500
        )
        
        st.markdown("### Belief Distribution")
        
        fig = px.histogram(
            df,
            x='current_belief',
            nbins=20,
            labels={"current_belief": "Belief Value", "count": "Count"},
            title="Distribution of Current Beliefs"
        )
        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Recent Movers")
        recent_updates = fetch_data("/api/beliefs/updates/recent", {"limit": 20})
        
        if recent_updates:
            movers_df = pd.DataFrame(recent_updates)
            movers_df['delta'] = (movers_df['posterior_belief'] - movers_df['prior_belief']).abs()
            movers_df = movers_df.nlargest(10, 'delta')
            
            for _, row in movers_df.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{row['statement'][:80]}...**")
                        st.caption(f"Updated: {row['created_at']}")
                    
                    with col2:
                        render_delta_badge(row['prior_belief'], row['posterior_belief'])
                    
                    st.divider()
    else:
        st.info("No beliefs found")

st.divider()
st.caption("Nexus v0.1.0 - Investment Research System")
