"""Streamlit UI for Nexus"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://api:8000"

st.set_page_config(
    page_title="Nexus - Investment Research System",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Nexus - Investment Research System")

page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Hypotheses", "Evidence", "Investigations", "Beliefs"]
)

if page == "Dashboard":
    st.header("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Hypotheses", "12")
    
    with col2:
        st.metric("Recent Updates", "8")
    
    with col3:
        st.metric("Pending Investigations", "3")
    
    st.subheader("Recent Belief Updates")
    
    try:
        response = requests.get(f"{API_URL}/api/beliefs/updates/recent?limit=10")
        if response.status_code == 200:
            updates = response.json()
            
            if updates:
                df = pd.DataFrame(updates)
                df['delta_pct'] = ((df['posterior_belief'] - df['prior_belief']) * 100).round(2)
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    df[['statement', 'prior_belief', 'posterior_belief', 'delta_pct', 'uncertainty', 'created_at']],
                    use_container_width=True
                )
            else:
                st.info("No recent belief updates")
        else:
            st.error(f"Failed to fetch updates: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")

elif page == "Hypotheses":
    st.header("Hypotheses")
    
    try:
        response = requests.get(f"{API_URL}/api/hypotheses/?limit=50")
        if response.status_code == 200:
            hypotheses = response.json()
            
            if hypotheses:
                df = pd.DataFrame(hypotheses)
                df['current_belief'] = df['current_belief'].fillna(0.5).round(3)
                
                st.dataframe(
                    df[['statement', 'hypothesis_type', 'current_belief', 'status']],
                    use_container_width=True
                )
                
                selected_id = st.selectbox(
                    "Select hypothesis for details",
                    options=[h['id'] for h in hypotheses],
                    format_func=lambda x: next(h['statement'][:50] for h in hypotheses if h['id'] == x)
                )
                
                if selected_id:
                    detail_response = requests.get(f"{API_URL}/api/hypotheses/{selected_id}")
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        
                        st.subheader("Hypothesis Details")
                        st.write(f"**Statement:** {details['statement']}")
                        st.write(f"**Current Belief:** {details.get('current_belief', 0.5):.3f}")
                        st.write(f"**Uncertainty:** {details.get('uncertainty', 0):.3f}")
                        
                        history_response = requests.get(f"{API_URL}/api/hypotheses/{selected_id}/history")
                        if history_response.status_code == 200:
                            history = history_response.json()
                            
                            if history:
                                st.subheader("Belief History")
                                history_df = pd.DataFrame(history)
                                history_df['created_at'] = pd.to_datetime(history_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                                
                                st.line_chart(history_df.set_index('created_at')['posterior_belief'])
            else:
                st.info("No hypotheses found")
        else:
            st.error(f"Failed to fetch hypotheses: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")

elif page == "Evidence":
    st.header("Evidence")
    
    source_type = st.selectbox("Filter by source type", ["All", "filing", "transcript", "hiring", "news"])
    
    try:
        if source_type == "All":
            response = requests.get(f"{API_URL}/api/evidence/?limit=50")
        else:
            response = requests.get(f"{API_URL}/api/evidence/?source_type={source_type}&limit=50")
        
        if response.status_code == 200:
            evidence = response.json()
            
            if evidence:
                df = pd.DataFrame(evidence)
                st.dataframe(
                    df[['title', 'source_type', 'source_date', 'validation_status']],
                    use_container_width=True
                )
            else:
                st.info("No evidence found")
        else:
            st.error(f"Failed to fetch evidence: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")

elif page == "Investigations":
    st.header("Investigations")
    
    status_filter = st.selectbox("Filter by status", ["All", "pending", "in_progress", "completed"])
    
    try:
        if status_filter == "All":
            response = requests.get(f"{API_URL}/api/investigations/?limit=50")
        else:
            response = requests.get(f"{API_URL}/api/investigations/?status={status_filter}&limit=50")
        
        if response.status_code == 200:
            investigations = response.json()
            
            if investigations:
                df = pd.DataFrame(investigations)
                st.dataframe(
                    df[['investigation_type', 'priority', 'status', 'trigger_reason']],
                    use_container_width=True
                )
            else:
                st.info("No investigations found")
        else:
            st.error(f"Failed to fetch investigations: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")

elif page == "Beliefs":
    st.header("Current Beliefs")
    
    try:
        response = requests.get(f"{API_URL}/api/beliefs/current?limit=100")
        if response.status_code == 200:
            beliefs = response.json()
            
            if beliefs:
                df = pd.DataFrame(beliefs)
                df['current_belief'] = df['current_belief'].round(3)
                df['uncertainty'] = df['uncertainty'].round(3)
                df['last_updated'] = pd.to_datetime(df['last_updated']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    df[['statement', 'current_belief', 'uncertainty', 'last_updated']],
                    use_container_width=True
                )
                
                st.subheader("Belief Distribution")
                st.bar_chart(df['current_belief'].value_counts().sort_index())
            else:
                st.info("No beliefs found")
        else:
            st.error(f"Failed to fetch beliefs: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
