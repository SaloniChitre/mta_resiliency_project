import pandas as pd
import folium
from folium.plugins import Search
import os
import json

def create_interactive_map():
    print("--- 🔍 Generating Searchable Digital Twin ---")
    
    # 1. Load Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # 2. Initialize Map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles='cartodbpositron')
    
    # 3. Draw Edges (Tracks) first
    coords = {str(row['stop_id']): [row['stop_lat'], row['stop_lon']] for _, row in hubs.iterrows()}
    edge_lines = [[coords[str(row['source'])], coords[str(row['target'])]] 
                  for _, row in edges.iterrows() 
                  if str(row['source']) in coords and str(row['target']) in coords]
    
    folium.PolyLine(edge_lines, color="gray", weight=1.5, opacity=0.3).add_to(m)

    # 4. Create GeoJSON-style features for the Search Plugin
    # This is the "Secret Sauce" to make Search work
    features = []
    for _, row in hubs.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['stop_lon'], row['stop_lat']] # GeoJSON is [Lon, Lat]
            },
            'properties': {
                'name': str(row['stop_name']),
                'stop_id': str(row['stop_id'])
            }
        }
        features.append(feature)

    geojson_data = {'type': 'FeatureCollection', 'features': features}

    # 5. Add Searchable GeoJson Layer
    # We make it invisible (opacity=0) because we will put CircleMarkers on top
    # but the Search bar needs this layer to "read" the names
    search_layer = folium.GeoJson(
        geojson_data,
        name="Search Layer",
        settings={'opacity': 0}, 
        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Station:'])
    ).add_to(m)

    # 6. Add Visible Markers
    for _, row in hubs.iterrows():
        folium.CircleMarker(
            location=[row['stop_lat'], row['stop_lon']],
            radius=5,
            color='blue',
            fill=True,
            fill_opacity=0.7,
            popup=f"<b>{row['stop_name']}</b>"
        ).add_to(m)

    # 7. Activate Search Bar
    Search(
        layer=search_layer,
        geom_type='Point',
        placeholder='Search for a station (e.g. Times Sq)...',
        collapsed=False,
        search_label='name',
        search_zoom=15
    ).add_to(m)

    # 8. Save
    os.makedirs('plots', exist_ok=True)
    m.save('plots/interactive_subway_map.html')
    print("✅ Success! Search should now be fully functional.")

if __name__ == "__main__":
    create_interactive_map()