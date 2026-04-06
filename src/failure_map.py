import pandas as pd
import folium
import numpy as np
import os
from folium.plugins import Fullscreen

class MockWeatherService:
    def __init__(self):
        self.storm_center = [40.6841, -73.9785] # Brooklyn Eye
        self.max_intensity = 8.5 
        self.storm_radius = 0.08 

    def get_rainfall(self, lat, lon):
        dist = np.sqrt((lat - self.storm_center[0])**2 + (lon - self.storm_center[1])**2)
        return round(max(8.5 * (1 - (dist / 0.08)), 0.5), 2) if dist < 0.08 else 0.8

def generate_connected_map(threshold=4.0):
    print("\n" + "="*60)
    print("🛰️  MTA DIGITAL TWIN: MAPPING CONNECTED INFRASTRUCTURE")
    print("="*60)
    
    # 1. Load and Align Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/weather_aware_edges.csv')
    
    # FORCE ID ALIGNMENT (Crucial for the lines to appear)
    hubs['stop_id'] = hubs['stop_id'].astype(str).str.strip()
    edges['source'] = edges['source'].astype(str).str.strip()
    edges['target'] = edges['target'].astype(str).str.strip()

    weather = MockWeatherService()
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12, tiles='cartodbpositron')
    Fullscreen().add_to(m)

    # Dictionary for fast coordinate lookup
    pos = {row['stop_id']: [row['stop_lat'], row['stop_lon']] for _, row in hubs.iterrows()}
    names = {row['stop_id']: row['stop_name'] for _, row in hubs.iterrows()}

    # 2. DRAW THE CONNECTIONS (EDGES)
    edge_count = 0
    for _, row in edges.iterrows():
        u, v = row['source'], row['target']
        
        if u in pos and v in pos:
            # Check rain at midpoint of the connection
            mid_lat = (pos[u][0] + pos[v][0]) / 2
            mid_lon = (pos[u][1] + pos[v][1]) / 2
            rain = weather.get_rainfall(mid_lat, mid_lon)
            
            # Visual logic for the "Subsequent Connection"
            is_cut = rain >= threshold
            color = '#ff4757' if is_cut else '#2f3542' # Red if severed, Dark Grey if active
            weight = 4 if is_cut else 1.5
            
            folium.PolyLine(
                locations=[pos[u], pos[v]],
                color=color, weight=weight, opacity=0.7,
                tooltip=f"<b>Connection:</b> {names.get(u)} ↔ {names.get(v)}<br><b>Status:</b> {'⚠️ SEVERED' if is_cut else '✅ ACTIVE'}"
            ).add_to(m)
            edge_count += 1

    # 3. DRAW THE HUBS (NODES)
    for _, hub in hubs.iterrows():
        s_id = hub['stop_id']
        rain = weather.get_rainfall(hub['stop_lat'], hub['stop_lon'])
        
        is_flooded = rain >= threshold
        folium.CircleMarker(
            location=[hub['stop_lat'], hub['stop_lon']],
            radius=5 if is_flooded else 3,
            color='#c0392b' if is_flooded else '#2ed573',
            fill=True,
            fill_opacity=0.9,
            tooltip=f"<b>Hub:</b> {hub['stop_name']}<br><b>Rain:</b> {rain}mm/hr"
        ).add_to(m)

    # 4. Save Output
    if not os.path.exists('plots'): os.makedirs('plots')
    m.save('plots/mta_connected_graph.html')
    print(f"✅ SUCCESS: Mapped {len(hubs)} Hubs and {edge_count} Connections.")
    print("🔗 Open: plots/mta_connected_graph.html")

if __name__ == "__main__":
    generate_connected_map(4.0)