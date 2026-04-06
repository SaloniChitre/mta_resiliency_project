import pandas as pd
import folium
import numpy as np
import os
from folium.plugins import Fullscreen

# --- EMBEDDED WEATHER ENGINE ---
class MockWeatherService:
    def __init__(self):
        self.storm_center = [40.6841, -73.9785] # Brooklyn Storm
        self.max_intensity = 8.5 
        self.storm_radius = 0.08 

    def get_rainfall(self, lat, lon):
        dist = np.sqrt((lat - self.storm_center[0])**2 + (lon - self.storm_center[1])**2)
        if dist < self.storm_radius:
            rain = self.max_intensity * (1 - (dist / self.storm_radius))
            return round(max(rain, 0.5), 2)
        return round(np.random.uniform(0, 1.2), 2)

def run_spatial_twin(threshold=4.0):
    print("\n🛰️  MTA DIGITAL TWIN: GENERATING LIVE SPATIAL RISK MAP...")
    
    # Load Data
    try:
        hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
        edges = pd.read_csv('data/processed/weather_aware_edges.csv')
    except Exception as e:
        print(f"❌ DATA ERROR: CSV files not found. Check data/processed/. {e}")
        return

    weather = MockWeatherService()
    coords = {str(row['stop_id']): [row['stop_lat'], row['stop_lon']] for _, row in hubs.iterrows()}
    names = {str(row['stop_id']): row['stop_name'] for _, row in hubs.iterrows()}
    
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12, tiles='cartodbpositron')
    Fullscreen().add_to(m)

    critical_count = 0
    for _, row in edges.iterrows():
        u, v = str(row['source']), str(row['target'])
        if u in coords and v in coords:
            mid_lat = (coords[u][0] + coords[v][0]) / 2
            mid_lon = (coords[u][1] + coords[v][1]) / 2
            rain = weather.get_rainfall(mid_lat, mid_lon)
            
            is_failed = rain >= threshold
            color = '#e74c3c' if is_failed else '#3498db'
            if is_failed: critical_count += 1

            folium.PolyLine(
                locations=[coords[u], coords[v]],
                color=color, weight=5 if is_failed else 2, opacity=0.8,
                tooltip=f"Segment: {names.get(u)} ↔ {names.get(v)}<br>Live Rain: {rain}mm/hr"
            ).add_to(m)

    if not os.path.exists('plots'): os.makedirs('plots')
    m.save('plots/mta_live_risk_map.html')
    print(f"✅ MAP GENERATED: {critical_count} segments identified as CRITICAL.")

if __name__ == "__main__":
    run_spatial_twin(4.0)