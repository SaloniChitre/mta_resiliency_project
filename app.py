import streamlit as st
import pandas as pd
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
import numpy as np
import random

# --- EXTERNAL LOGIC ENGINES ---
from monte_carlo_simulations import run_cluster_monte_carlo

# --- 0. HELPER FUNCTIONS ---
def plot_asset_risk(intensity, load_mult):
    """Generates the exponential risk curve for the analytics section."""
    x = np.linspace(1, 10, 10)
    y = (x**2) * 10000 * load_mult
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, 
        mode='lines+markers', 
        line=dict(color='#ff4b4b', width=3),
        marker=dict(size=8, color='#ff4b4b')
    ))
    fig.update_layout(
        title="📈 Asset Risk vs. Rainfall Intensity",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"), 
        height=350,
        xaxis=dict(title="Intensity (mm/hr)", gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(title="Est. Damage ($)", gridcolor="rgba(255,255,255,0.1)")
    )
    return fig

# --- 1. CONFIG & DATA LOADING ---
st.set_page_config(layout="wide", page_title="MTA Nexus | EOC Dashboard")

@st.cache_data
def load_hubs():
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

STRATEGY_MAP = {
    "Times Sq-42 St": {
        "bypass": "Grand Central (S Shuttle)", 
        "j_mz": "Divert M to 6th Ave via Christie St. Skip 14 St.", 
        "g_line": "Standby for LIC-Queens connection; increase G-S shuttle frequency.", 
        "bus": True
    },
    "34 St-Penn Station": {
        "bypass": "34 St-Herald Sq (B/D/F/M/N/Q/R/W)", 
        "j_mz": "J/Z: Increase headways to 8m. M: Terminate at Essex St.", 
        "g_line": "No impact; maintain standard G-line headways.", 
        "bus": True
    },
    "14 St-Union Sq": {
        "bypass": "14 St-6 Av (F/M/L)", 
        "j_mz": "Terminate J at Chambers St. Divert M to Broadway Local.", 
        "g_line": "Deploy 8-car sets for Brooklyn bypass support.", 
        "bus": True
    },
    "Fulton St": {
        "bypass": "WTC Cortlandt (1)", 
        "j_mz": "J/Z: Terminate at Broad St. No M service south of Delancey.", 
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
    sim_month = st.selectbox("Simulation Month (2026):", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=11)
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
    
    unique_stations = sorted(hubs['stop_name'].unique())
    selected_hub = st.selectbox("Active Monitoring Hub:", unique_stations)
    
    intensity = st.slider("Rainfall Intensity (mm/hr)", 1.0, 10.0, 4.0, step=0.5)
    st.subheader("🛡️ Mitigation Response")
    deploy_mitigation = st.checkbox("Deploy Emergency Pumps & Gates", value=False)
    
    if st.button("🚀 Force Simulation Refresh"):
        st.session_state.current_seed = random.randint(1, 99999)
        st.cache_data.clear()

# --- 4. DYNAMIC SIMULATION ENGINE ---

# UPDATE: Load multiplier is calculated first so the simulation can use it
current_load_mult = 1.0
node_status = "STABLE"
if enable_event:
    event_hub_keyword = active_event.get('hub', 'N/A')
    if event_hub_keyword.lower() in selected_hub.lower():
        current_load_mult = active_event['mult']
        node_status = "PRIMARY EVENT HUB"

main_hub_data = hubs[hubs['stop_name'] == selected_hub].iloc[0]
hubs['dist_to_selected'] = np.sqrt((hubs['stop_lat'] - main_hub_data['stop_lat'])**2 + (hubs['stop_lon'] - main_hub_data['stop_lon'])**2)
adjacent_neighbors = hubs[(hubs['dist_to_selected'] <= 0.012) & (hubs['stop_name'] != selected_hub)]

@st.cache_data
def get_stable_simulation(stop_name, intensity_val, mitigation_active, load_val, seed):
    np.random.seed(seed)
    # Simulation now accepts the event load multiplier as a factor
    return run_cluster_monte_carlo(main_hub_data, adjacent_neighbors, intensity=intensity_val, mitigation=mitigation_active, load_mult=load_val)

mc_results = get_stable_simulation(selected_hub, intensity, deploy_mitigation, current_load_mult, st.session_state.current_seed)

failure_prob = mc_results['failure_prob']
is_critical = failure_prob > 30.0 

mitigation_boost = 0.4 if deploy_mitigation else 0.0
# Radius is now truly dynamic based on simulation failure probability
cascade_radius = (failure_prob / 100) * 0.045 * (1.0 - (mitigation_boost * 0.5)) 

hub_strategy = STRATEGY_MAP.get(selected_hub, {
    "bypass": "Nearest Safe Node", 
    "j_mz": "Standard system-wide headways.", 
    "g_line": "Standard 4-car local operations.", 
    "bus": False
})

affected_neighbors_df = pd.DataFrame()
if enable_event:
    event_hub_keyword = active_event.get('hub', 'N/A')
    event_hub_matches = hubs[hubs['stop_name'].str.contains(event_hub_keyword, case=False, na=False)]
    if not event_hub_matches.empty:
        e_lat, e_lon = event_hub_matches.iloc[0]['stop_lat'], event_hub_matches.iloc[0]['stop_lon']
        hubs['dist_to_event'] = np.sqrt((hubs['stop_lat'] - e_lat)**2 + (hubs['stop_lon'] - e_lon)**2)
        if node_status != "PRIMARY EVENT HUB" and hubs.loc[hubs['stop_name'] == selected_hub, 'dist_to_event'].values[0] < 0.015:
            node_status = "AFFECTED NEIGHBOR"
        affected_neighbors_df = hubs[(hubs['dist_to_event'] < 0.015) & (hubs['stop_name'] != selected_hub)]

if is_critical:
    all_affected_nodes = hubs[(hubs['dist_to_selected'] <= cascade_radius) & (hubs['stop_name'] != selected_hub)]
    total_impacted = int((main_hub_data['daily_ridership'] * current_load_mult) + all_affected_nodes['daily_ridership'].sum())
    
    if hub_strategy["bypass"] == "Nearest Safe Node":
        alt_candidates = hubs[hubs['dist_to_selected'] > cascade_radius]
        alt_path = alt_candidates.nsmallest(1, 'dist_to_selected').iloc[0]['stop_name'] if not alt_candidates.empty else "N/A"
    else:
        alt_path = hub_strategy["bypass"]
else:
    all_affected_nodes = pd.DataFrame()
    total_impacted = int(main_hub_data['daily_ridership'] * current_load_mult)
    alt_path = "N/A"

# --- 5. DASHBOARD HEADER & KPIS ---
st.title("🚇 MTA NEXUS: EMERGENCY OPERATIONS CENTER")
display_context = active_event['name'] if current_load_mult > 1.0 else "Standard Operations"
st.markdown(f"**Scenario:** {sim_month} 2026 | **Node Status:** {node_status} | **Context:** {display_context}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Commuters Impacted", f"{total_impacted:,}", delta=f"+{int((current_load_mult-1)*100)}% Surge" if current_load_mult > 1 else None, delta_color="inverse")
k2.metric("Failure Probability", f"{failure_prob:.1f}%", delta=f"{intensity} mm/hr Load", delta_color="inverse")
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
            folium.PolyLine(locations=[[main_hub_data['stop_lat'], main_hub_data['stop_lon']], [node['stop_lat'], node['stop_lon']]], color="#e67e22", weight=1.5, opacity=0.6).add_to(m)
            folium.CircleMarker([node['stop_lat'], node['stop_lon']], radius=8, color="#e67e22", fill=True, fill_opacity=0.7,
                tooltip=folium.Tooltip(f"<b>NODE:</b> {node['stop_name']}<br><b>STATUS:</b> Cascade Risk<br><b>LOAD:</b> {int(node['daily_ridership']):,}")).add_to(m)

    if not affected_neighbors_df.empty:
        for _, neighbor in affected_neighbors_df.iterrows():
            folium.PolyLine(locations=[[main_hub_data['stop_lat'], main_hub_data['stop_lon']], [neighbor['stop_lat'], neighbor['stop_lon']]], color="#3498db", weight=1, opacity=0.4, dash_array='5, 5').add_to(m)
            folium.CircleMarker([neighbor['stop_lat'], neighbor['stop_lon']], radius=6, color="#3498db", fill=True, fill_opacity=0.6,
                tooltip=folium.Tooltip(f"<b>SURGE:</b> {neighbor['stop_name']}<br><b>MULT:</b> {current_load_mult:.2f}x")).add_to(m)

    folium.Marker([main_hub_data['stop_lat'], main_hub_data['stop_lon']], icon=folium.Icon(color='red' if is_critical else 'blue', icon='warning', prefix='fa'), tooltip=folium.Tooltip(f"<b>PRIMARY HUB:</b> {selected_hub}")).add_to(m)
    st_folium(m, width=850, height=500, key="mta_nexus_map")

with col_action:
    st.subheader("🛠️ EOC Strategic Action Plan")
    if is_critical:
        st.error(f"🚨 SECTOR THREAT: {failure_prob:.0f}% PROBABILITY")
        st.markdown(f"### 🚇 Subway Rerouting: {selected_hub}")
        st.write(f"**Primary Bypass:** {alt_path}")
        re_cols = st.columns(2)
        re_cols[0].info(f"**J/M/Z Lines**\n\n{hub_strategy['j_mz']}")
        re_cols[1].info(f"**G Line**\n\n{hub_strategy['g_line']}")
        st.markdown("### 🚌 Surface Operations")
        if hub_strategy["bus"]: st.success("✅ **Bus Bridge Active**")
        else: st.info("Bus Bridge Standby")
        st.markdown("### 🔧 Engineering Checklist")
        st.checkbox("Seal East River Flood Gates", value=is_critical)
        st.checkbox("Deploy Pump Train to Sector", value=intensity > 6.5)
        st.error(f"Projected Asset Risk: **${(intensity * 220000 * current_load_mult):,.0f}**")
    else:
        st.success("✅ **SYSTEM NOMINAL**")

# --- 7. ANALYTICS ---
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    st.subheader("🕸️ Hub Stress Radar Chart")
    i_risk = min(100, (main_hub_data['physical_risk_score'] * intensity * 10))
    r_load = min(100, (current_load_mult * 20))
    age_stress, iso_stress = (80 if "St" in selected_hub else 45), (min(100, (len(all_affected_nodes) * 15)) if is_critical else 10)
    pwr_stress = 90 if deploy_mitigation and intensity > 6 else 35
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=[failure_prob, r_load, age_stress, iso_stress, pwr_stress], theta=['Inundation Risk', 'Ridership Load', 'Infrastructure Age', 'Network Isolation', 'Power Grid Stress'], fill='toself', line_color='#00FFCC', fillcolor='rgba(0, 255, 204, 0.3)'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="gray"), bgcolor="rgba(0,0,0,0)"), template="plotly_dark", height=380, margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig_radar, use_container_width=True)

with c2:
    fig_risk = plot_asset_risk(intensity, current_load_mult)
    st.plotly_chart(fig_risk, use_container_width=True)

with c3:
    st.subheader("📋 Monte Carlo Simulation Logs")
    log_df = mc_results['raw_data'].copy().head(10)
    log_df.columns = ["Sim Rain", "Node Fail", "Neighbors Hit"]
    log_df['Node Fail'] = log_df['Node Fail'].apply(lambda x: "🔴 FAIL" if x else "🟢 OK")
    st.dataframe(log_df, use_container_width=True)