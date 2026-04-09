import streamlit as st
import pandas as pd
import folium
import plotly.graph_objects as go
from streamlit_folium import st_folium
import numpy as np
import random
import networkx as nx
import sys
import os

# --- IMPORT FIX ---
sys.path.append(os.path.dirname(__file__))

try:
    from monte_carlo_simulations import run_cluster_monte_carlo
    from rerouting_engine import build_mta_graph, get_agentic_path
except ImportError:
    st.error("❌ Could not find 'monte_carlo_simulations.py' or 'rerouting_engine.py'.")
    st.stop()

# --- 0. HELPER FUNCTIONS ---
def plot_asset_risk(intensity, load_mult):
    x = np.linspace(1, 10, 10)
    y = (x**2.2) * 8500 * load_mult 
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#ff4b4b', width=3)))
    fig.update_layout(title="📈 Projected Asset Exposure ($)", paper_bgcolor='rgba(0,0,0,0)', 
                      plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=350)
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

hubs = load_hubs()

# --- 2. SESSION STATE ---
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = 42

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b3/MTA_NYC_Logo.svg", width=80)
    st.header("🕹️ EOC Console")
    sim_month = st.selectbox("Simulation Month (2026):", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=3)
    enable_event = st.checkbox("Simulate High-Load Event", value=True)
    selected_hub = st.selectbox("Focus Station:", sorted(hubs['stop_name'].unique()))
    intensity = st.slider("Rainfall Intensity (mm/hr)", 1.0, 10.0, 6.5, step=0.5)
    deploy_mitigation = st.checkbox("Activate Emergency Pumps", value=False)
    
    if st.button("🚀 Run Monte Carlo Iteration"):
        st.session_state.current_seed = random.randint(1, 99999)
        st.cache_data.clear()

# --- 4. DYNAMIC SIMULATION ENGINE ---
current_load_mult = 3.8 if enable_event else 1.0
main_hub_data = hubs[hubs['stop_name'] == selected_hub].iloc[0]

hubs['dist_to_selected'] = np.sqrt((hubs['stop_lat'] - main_hub_data['stop_lat'])**2 + (hubs['stop_lon'] - main_hub_data['stop_lon'])**2)
adjacent_neighbors = hubs[(hubs['dist_to_selected'] <= 0.015) & (hubs['stop_name'] != selected_hub)]

@st.cache_data
def get_stable_simulation(stop_name, intensity_val, mitigation_active, load_val, seed):
    np.random.seed(seed)
    return run_cluster_monte_carlo(main_hub_data, adjacent_neighbors, intensity=intensity_val, mitigation=mitigation_active, load_mult=load_val)

mc_results = get_stable_simulation(selected_hub, intensity, deploy_mitigation, current_load_mult, st.session_state.current_seed)
failure_prob = mc_results['failure_prob']
neighbor_probs = mc_results.get('neighbor_probs', {})
is_critical = failure_prob > 30.0 

intensity_map = {selected_hub: failure_prob / 100}
isolated_nodes_count = 0

for n_name, n_prob in neighbor_probs.items():
    intensity_map[n_name] = n_prob / 100
    if n_prob > 30.0: isolated_nodes_count += 1

G_mta = build_mta_graph(hubs)
target = "116 St-Columbia University" if selected_hub != "116 St-Columbia University" else "Grand Central"
dynamic_path = get_agentic_path(G_mta, selected_hub, target, intensity_map)

mitigation_factor = 0.5 if deploy_mitigation else 1.0
cascade_radius = (failure_prob / 100) * 0.045 * mitigation_factor

# --- 5. DASHBOARD HEADER & KPIS ---
st.title("🚇 MTA NEXUS: EMERGENCY OPERATIONS")

k1, k2, k3, k4 = st.columns(4)

# Only show high risk numbers if the probability is above 10%
impacted_display = int(main_hub_data['daily_ridership'] * current_load_mult) if failure_prob > 10 else 0

k1.metric(
    "Commuters at Risk", 
    f"{impacted_display:,}", 
    delta=f"{isolated_nodes_count} Nodes Impacted" if failure_prob > 10 else "Baseline Load",
    delta_color="inverse"
)

# Inundation Prob stays as is to show the raw risk
k2.metric("Inundation Probability", f"{failure_prob:.1f}%", delta=f"{intensity}mm/hr Storm", delta_color="inverse")

# Clear the bypass target if there's no risk
bypass_station = dynamic_path[1] if (len(dynamic_path) > 1 and is_critical) else "ROUTING NORMAL"
k3.metric("Bypass Target", bypass_station)

eti = "STABILIZED" if deploy_mitigation and is_critical else f"{int(max(80 - (intensity * 7), 5))} min"
k4.metric("Est. Time to Flood", eti if failure_prob > 15.0 else "SECURE")

# --- 6. INTERACTIVE MAP ---
col_map, col_action = st.columns([2, 1])

with col_map:
    # Initialize Map
    m = folium.Map(location=[main_hub_data['stop_lat'], main_hub_data['stop_lon']], zoom_start=14, tiles="CartoDB dark_matter")
    
    # 1. Cascade Risk Area (Visual Circle)
    if failure_prob > 10:
        folium.Circle([main_hub_data['stop_lat'], main_hub_data['stop_lon']], 
                      radius=cascade_radius * 100000, color='red', fill=True, fill_opacity=0.2).add_to(m)

    # 2. Connection Lines to Neighboring Nodes
    impacted_nodes = hubs[(hubs['dist_to_selected'] <= cascade_radius) & (hubs['stop_name'] != selected_hub)]
    for _, node in impacted_nodes.iterrows():
        # Draw the line (Edge)
        folium.PolyLine(
            locations=[[main_hub_data['stop_lat'], main_hub_data['stop_lon']], [node['stop_lat'], node['stop_lon']]],
            color="#e67e22", weight=2, opacity=0.6, dash_array='5, 5'
        ).add_to(m)
        
        # Draw the node (Marker)
        folium.CircleMarker(
            [node['stop_lat'], node['stop_lon']],
            radius=5, color="#e67e22", fill=True,
            tooltip=f"Impacted Node: {node['stop_name']}"
        ).add_to(m)

    # 3. Dynamic Reroute Path (The 'Edges' for the evacuation route)
    if len(dynamic_path) > 1:
        path_coords = []
        for p in dynamic_path:
            node_data = hubs[hubs['stop_name'] == p]
            if not node_data.empty:
                lat, lon = node_data.iloc[0]['stop_lat'], node_data.iloc[0]['stop_lon']
                path_coords.append([lat, lon])
                # Small markers to enable hover along the route
                folium.CircleMarker(
                    [lat, lon], radius=3, color="#00FFCC", fill=True,
                    tooltip=f"Route Station: {p}"
                ).add_to(m)
        
        if len(path_coords) > 1:
            folium.PolyLine(
                path_coords, color="#00FFCC", weight=6, opacity=0.8, 
                tooltip="Emergency Evacuation Route"
            ).add_to(m)

    # 4. Main Hub Marker
    folium.Marker(
        [main_hub_data['stop_lat'], main_hub_data['stop_lon']], 
        icon=folium.Icon(color='red' if is_critical else 'blue', icon='warning', prefix='fa'),
        tooltip=f"<b>{selected_hub}</b><br>Risk: {failure_prob:.1f}%"
    ).add_to(m)
    
    # Render the map ONLY ONCE
    st_folium(m, width=850, height=500, key=f"nexus_map_{st.session_state.current_seed}")

with col_action:
    st.subheader("🛠️ Tactical Action Plan")
    if is_critical:
        st.error(f"🚨 HAZARD DETECTED")
        st.markdown(f"**Recommended Evacuation:**")
        st.success(f"Path: {' → '.join(dynamic_path[:4])}")
        st.warning("Action: Divert all downtown traffic to 7-Line Bypass.")
    else:
        st.success("✅ SYSTEM NOMINAL")

# --- 7. ANALYTICS (Stacked Layout) ---
st.divider()

# Stress Radar Section
st.subheader("🕸️ System Stress Analysis")
node_iso_score = min(isolated_nodes_count * 20, 100)
fig_radar = go.Figure(go.Scatterpolar(
    r=[failure_prob, (current_load_mult * 25), 45, node_iso_score, 30],
    theta=['Inundation Risk', 'Ridership Load', 'Infra Age', 'Node Isolation', 'Grid Stress'],
    fill='toself', 
    line_color='#00FFCC', 
    fillcolor='rgba(0, 255, 204, 0.2)'
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
    template="plotly_dark", 
    height=500, # Increased height for clarity
    margin=dict(t=50, b=50)
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# Asset Exposure Section
st.subheader("📉 Financial Risk Modeling")
st.plotly_chart(plot_asset_risk(intensity, current_load_mult), use_container_width=True)

st.divider()

# Telemetry Data Section
st.subheader("📋 Cluster Telemetry")
if neighbor_probs:
    log_data = [{"Node": k, "Risk": f"{v:.1f}%", "Status": "🚨 FAIL" if v > 30 else "✅ OK"} for k, v in neighbor_probs.items()]
    # Using container width for the table to match the charts
    st.dataframe(pd.DataFrame(log_data), use_container_width=True)