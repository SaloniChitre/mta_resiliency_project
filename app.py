import streamlit as st
import pandas as pd
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
import numpy as np
import random

# --- EXTERNAL LOGIC ENGINES ---
from monte_carlo_simulations import run_cluster_monte_carlo
# Removed external rerouting_engine import to use hardcoded logic below

# --- 1. CONFIG & DATA LOADING ---
st.set_page_config(layout="wide", page_title="MTA Nexus | EOC Dashboard")

@st.cache_data
def load_hubs():
    # Ensure this file path is correct in your local environment
    df = pd.read_csv('data/processed/cleaned_hubs.csv')
    flood_prone = ["Times Sq-42 St", "34 St-Penn Station", "28 St", "23 St", "14 St-Union Sq", "Queens Plaza"]
    df['physical_risk_score'] = df['stop_name'].apply(lambda x: 0.85 if x in flood_prone else 0.15)
    df['daily_ridership'] = df['stop_name'].apply(lambda x: (abs(hash(x)) % 65000) + 12000)
    return df

YEARLY_EVENTS = {
    "Jan": [{"hub": "Times Sq", "name": "NYE Cleanup Operations", "mult": 2.2}],
    "Feb": [{"hub": "34 St", "name": "Westminster Dog Show (MSG)", "mult": 1.8}],
    "Mar": [{"hub": "42 St", "name": "St. Patrick's Day Parade", "mult": 3.1}],
    "Apr": [{"hub": "Mets-Willets", "name": "MLB Opening Day", "mult": 3.5}],
    "May": [{"hub": "Union Sq", "name": "NYC Bike Expo", "mult": 2.4}],
    "Jun": [{"hub": "Christopher", "name": "NYC Pride March", "mult": 4.0}],
    "Jul": [{"hub": "Fulton St", "name": "July 4th Fireworks", "mult": 3.5}],
    "Aug": [{"hub": "Mets-Willets", "name": "US Open Tennis", "mult": 3.2}],
    "Sep": [{"hub": "Grand Central", "name": "UN General Assembly", "mult": 2.8}],
    "Oct": [{"hub": "W 4 St", "name": "Village Halloween Parade", "mult": 3.7}],
    "Nov": [{"hub": "34 St", "name": "Thanksgiving Day Parade", "mult": 4.2}],
    "Dec": [{"hub": "Times Sq", "name": "New Year's Eve Celebration", "mult": 5.0}]
}

# --- HARDCODED STRATEGY MAP ---
STRATEGY_MAP = {
    "Times Sq-42 St": {
        "bypass": "Grand Central (S Shuttle)",
        "j_mz": "Divert M to 6th Ave via Christie St.",
        "g_line": "Standby for LIC-Queens connection.",
        "bus": True
    },
    "34 St-Penn Station": {
        "bypass": "34 St-Herald Sq (B/D/F/M/N/Q/R/W)",
        "j_mz": "Increase J/Z headways to 8m.",
        "g_line": "No impact; maintain standard ops.",
        "bus": True
    },
    "14 St-Union Sq": {
        "bypass": "14 St-6 Av (F/M/L)",
        "j_mz": "Terminate J at Chambers St.",
        "g_line": "Deploy 8-car sets for Brooklyn bypass.",
        "bus": True
    },
    "Fulton St": {
        "bypass": "WTC Cortlandt (1)",
        "j_mz": "Terminate J at Broad St.",
        "g_line": "Extend G to Church Av for surge relief.",
        "bus": False
    }
}

hubs = load_hubs()

# --- 2. SESSION STATE ---
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = 42

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b3/MTA_NYC_Logo.svg", width=80)
    st.header("🕹️ Simulation Console")
    
    sim_month = st.selectbox("Simulation Month (2026):", 
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=11)
    
    st.divider()
    st.subheader("🎭 Event Overlay")
    enable_event = st.checkbox("Enable Event Load", value=False)
    
    active_event = {"name": "Standard Operations", "mult": 1.0, "hub": "N/A"}
    if enable_event:
        month_events = YEARLY_EVENTS.get(sim_month, [])
        if month_events:
            event_choice = st.selectbox("Trigger Event:", [e["name"] for e in month_events])
            active_event = next(e for e in month_events if e["name"] == event_choice)

    st.divider()
    selected_hub = st.selectbox("Active Monitoring Hub:", hubs['stop_name'].sort_values())
    intensity = st.slider("Rainfall Intensity (mm/hr)", 1.0, 10.0, 4.0, step=0.5)
    
    st.subheader("🛡️ Mitigation Response")
    deploy_mitigation = st.checkbox("Deploy Emergency Pumps & Gates", value=False)
    
    if st.button("🚀 Force Simulation Refresh"):
        st.session_state.current_seed = random.randint(1, 99999)

# --- 4. DYNAMIC SIMULATION ENGINE ---
is_critical = intensity >= 4.0
main_hub_data = hubs[hubs['stop_name'] == selected_hub].iloc[0]

hubs['dist_to_selected'] = np.sqrt((hubs['stop_lat'] - main_hub_data['stop_lat'])**2 + 
                                   (hubs['stop_lon'] - main_hub_data['stop_lon'])**2)

adjacent_neighbors = hubs[(hubs['dist_to_selected'] <= 0.012) & (hubs['stop_name'] != selected_hub)]
mc_results = run_cluster_monte_carlo(main_hub_data, adjacent_neighbors)

mitigation_boost = 0.4 if deploy_mitigation else 0.0
cascade_radius = 0.025 * (1.0 - (mitigation_boost * 0.5)) 

# FIX: Rerouting logic now pulls from the STRATEGY_MAP
hub_strategy = STRATEGY_MAP.get(selected_hub, {
    "bypass": "Nearest Safe Node", 
    "j_mz": "Reduce headways to 6m system-wide.",
    "g_line": "Standard 4-car operations.",
    "bus": False
})

load_mult = 1.0
node_status = "STABLE"
affected_neighbors_df = pd.DataFrame()

if enable_event:
    event_hub_keyword = active_event.get('hub', 'N/A')
    event_hub_matches = hubs[hubs['stop_name'].str.contains(event_hub_keyword, case=False, na=False)]
    if not event_hub_matches.empty:
        e_lat, e_lon = event_hub_matches.iloc[0]['stop_lat'], event_hub_matches.iloc[0]['stop_lon']
        hubs['dist_to_event'] = np.sqrt((hubs['stop_lat'] - e_lat)**2 + (hubs['stop_lon'] - e_lon)**2)
        if event_hub_keyword.lower() in selected_hub.lower():
            load_mult = active_event['mult']
            node_status = "PRIMARY EVENT HUB"
        elif hubs.loc[hubs['stop_name'] == selected_hub, 'dist_to_event'].values[0] < 0.015:
            load_mult = 1.0 + (active_event['mult'] - 1.0) * 0.4
            node_status = "AFFECTED NEIGHBOR"
        affected_neighbors_df = hubs[(hubs['dist_to_event'] < 0.015) & (hubs['stop_name'] != selected_hub)]

if is_critical:
    all_affected_nodes = hubs[(hubs['dist_to_selected'] <= cascade_radius) & (hubs['stop_name'] != selected_hub)]
    total_impacted = int((main_hub_data['daily_ridership'] * load_mult) + all_affected_nodes['daily_ridership'].sum())
    
    # Calculate nearest safe node if hardcode is generic
    if hub_strategy["bypass"] == "Nearest Safe Node":
        alt_path_candidates = hubs[hubs['dist_to_selected'] > cascade_radius]
        alt_path = alt_path_candidates.nsmallest(1, 'dist_to_selected').iloc[0]['stop_name'] if not alt_path_candidates.empty else "N/A"
    else:
        alt_path = hub_strategy["bypass"]
else:
    all_affected_nodes = pd.DataFrame()
    total_impacted = int(main_hub_data['daily_ridership'] * load_mult)
    alt_path = "N/A"

# --- 5. DASHBOARD HEADER & KPIS ---
st.title("🚇 MTA NEXUS: EMERGENCY OPERATIONS CENTER")
display_context = active_event['name'] if load_mult > 1.0 else "Standard Operations"
st.markdown(f"**Scenario:** {sim_month} 2026 | **Node Status:** {node_status} | **Context:** {display_context}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Commuters Impacted", f"{total_impacted:,}", 
          delta=f"+{int((load_mult-1)*100)}% Surge" if load_mult > 1 else None, delta_color="inverse")

k2.metric("Failure Probability", f"{mc_results['failure_prob']:.1f}%", 
          delta="Risk High" if mc_results['failure_prob'] > 40 else "Nominal", delta_color="inverse")

k3.metric("Bypass Target", alt_path if is_critical else "Optimal", border=True)

eti = "STABILIZED" if deploy_mitigation and is_critical else f"{int(max(60 - (intensity * 5.8), 3))} min"
k4.metric("Est. Time to Inundation", eti if is_critical else "N/A")

st.divider()

# --- 6. INTERACTIVE MAP & ACTION PLAN ---
col_map, col_action = st.columns([2, 1])

with col_map:
    st.subheader("📍 Infrastructure Risk & Cascade Radius")
    m = folium.Map(location=[main_hub_data['stop_lat'], main_hub_data['stop_lon']], zoom_start=13, tiles="CartoDB dark_matter")
    
    if is_critical:
        folium.Circle([main_hub_data['stop_lat'], main_hub_data['stop_lon']], radius=cascade_radius * 100000, color='red', fill=True, fill_opacity=0.1).add_to(m)
        for _, node in all_affected_nodes.iterrows():
            folium.CircleMarker([node['stop_lat'], node['stop_lon']], radius=8, color="#e67e22", fill=True, fill_opacity=0.7).add_to(m)

    if not affected_neighbors_df.empty:
        for _, neighbor in affected_neighbors_df.iterrows():
            folium.CircleMarker(
                [neighbor['stop_lat'], neighbor['stop_lon']],
                radius=6, color="#3498db", fill=True, fill_opacity=0.6,
                tooltip=f"EVENT SURGE: {neighbor['stop_name']}"
            ).add_to(m)

    folium.Marker([main_hub_data['stop_lat'], main_hub_data['stop_lon']], icon=folium.Icon(color='red' if is_critical else 'blue')).add_to(m)
    st_folium(m, width=850, height=500)

with col_action:
    st.subheader("🛠️ EOC Strategic Action Plan")
    if is_critical:
        if intensity > 7.5: st.error("🚨 LEVEL 1: FULL SYSTEM ISOLATION")
        else: st.warning("⚠️ LEVEL 2: SECTOR CONTAINMENT")

        st.markdown("### 🚇 Subway Rerouting")
        st.write(f"**Primary Bypass:** {alt_path}")
        
        re_cols = st.columns(2)
        re_cols[0].info(f"**J/M/Z Lines**\n\n{hub_strategy['j_mz']}")
        re_cols[1].info(f"**G Line**\n\n{hub_strategy['g_line']}")

        st.markdown("### 🚌 Surface Operations")
        if hub_strategy["bus"]:
            st.success("✅ **Bus Bridge Active**")
        else:
            st.info("Bus Bridge Standby")

        st.markdown("### 🔧 Engineering Checklist")
        st.checkbox("Seal East River Flood Gates", value=is_critical)
        st.checkbox("Deploy Pump Train to Sector", value=intensity > 6.5)

        risk_val = (intensity * 220000 * load_mult)
        st.error(f"Projected Asset Risk: **${risk_val:,.0f}**")
    else:
        st.success("✅ **SYSTEM NOMINAL**")

# --- 7. LOGS & RADAR ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader("🕸️ Hub Stress Radar Chart")
    i_risk = min(100, (main_hub_data['physical_risk_score'] * intensity * 10))
    r_load = min(100, (load_mult * 20))
    age_stress = 80 if "St" in selected_hub else 45 
    iso_stress = min(100, (len(all_affected_nodes) * 15)) if is_critical else 10
    pwr_stress = 90 if deploy_mitigation and intensity > 6 else 35

    categories = ['Inundation Risk', 'Ridership Load', 'Infrastructure Age', 'Network Isolation', 'Power Grid Stress']
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[i_risk, r_load, age_stress, iso_stress, pwr_stress],
        theta=categories, fill='toself', line_color='#00FFCC', fillcolor='rgba(0, 255, 204, 0.3)'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="gray"), bgcolor="rgba(0,0,0,0)"),
        template="plotly_dark", height=400, margin=dict(l=80, r=80, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with c2:
    st.subheader("📋 Monte Carlo Simulation Logs")
    log_df = mc_results['raw_data'].copy().head(10)
    log_df.columns = ["Sim Rain", "Node Fail", "Neighbors Hit"]
    st.dataframe(log_df, use_container_width=True)