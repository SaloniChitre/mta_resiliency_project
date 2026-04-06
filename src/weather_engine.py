import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import os

def integrate_weather_to_network():
    print("--- 🌧️ Running Weather-to-Network Integration ---")
    
    # 1. Load Project Data
    try:
        hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
        edges = pd.read_csv('data/processed/network_edges.csv')
        weather = pd.read_csv('data/raw/noaa_nyc_2026.csv')
    except FileNotFoundError as e:
        print(f"❌ Missing data files: {e}")
        return

    # 2. Spatial Mapping (Nearest Neighbor)
    weather_coords = weather[['LATITUDE', 'LONGITUDE']].values
    tree = cKDTree(weather_coords)
    
    station_coords = hubs[['stop_lat', 'stop_lon']].values
    _, indices = tree.query(station_coords)
    
    # Assign precipitation to each station
    hubs['current_prcp'] = weather.iloc[indices]['PRCP'].values
    
    # 3. Calculate "Edge Risk" (The rain falling ON the track)
    prcp_map = pd.Series(hubs.current_prcp.values, index=hubs.stop_id.astype(str)).to_dict()
    
    edge_flood_scores = []
    for _, row in edges.iterrows():
        p1 = prcp_map.get(str(row['source']), 0)
        p2 = prcp_map.get(str(row['target']), 0)
        # We use the average of the two connected stations for the track intensity
        edge_flood_scores.append((p1 + p2) / 2)
        
    edges['flood_intensity'] = edge_flood_scores
    
    # 4. Save the Weather-Aware Network
    os.makedirs('data/processed', exist_ok=True)
    edges.to_csv('data/processed/weather_aware_edges.csv', index=False)
    print(f"✅ Network Updated: {len(edges)} tracks now have real-time flood scores.")

if __name__ == "__main__":
    integrate_weather_to_network()