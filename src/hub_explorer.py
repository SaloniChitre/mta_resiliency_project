import pandas as pd
import folium
from folium.plugins import MarkerCluster
import os

def create_hub_explorer():
    print("--- 🔍 Generating Hub Connectivity Explorer ---")
    
    # 1. Load Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # 2. Calculate Degree (Connectivity) for each station
    # Count how many times each station appears in the edges file
    all_connections = pd.concat([edges['source'], edges['target']])
    connectivity_counts = all_connections.value_counts().to_dict()
    
    # 3. Initialize Map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12, tiles='cartodbpositron')

    # 4. Filter for Main Hubs (Degree > 1)
    main_hubs = hubs[hubs['stop_id'].map(lambda x: connectivity_counts.get(str(x), 0) > 1)].copy()
    
    # 5. Build a "Neighbor Map" to see who is connected to who
    neighbors = {}
    for _, row in edges.iterrows():
        s, t = str(row['source']), str(row['target'])
        neighbors.setdefault(s, []).append(t)
        neighbors.setdefault(t, []).append(s)

    # Helper to get names from IDs
    id_to_name = pd.Series(hubs.stop_name.values, index=hubs.stop_id.astype(str)).to_dict()

    # 6. Add Hubs to Map
    for _, row in main_hubs.iterrows():
        stop_id = str(row['stop_id'])
        count = connectivity_counts.get(stop_id, 0)
        
        # Get names of all connected stations
        connected_ids = neighbors.get(stop_id, [])
        connected_names = [id_to_name.get(cid, "Unknown Station") for cid in connected_ids]
        connections_list = "<br>• ".join(connected_names)

        # Create a professional Popup
        popup_html = f"""
        <div style="width:200px">
            <h4 style="margin-bottom:5px">{row['stop_name']}</h4>
            <b>Connections:</b> {count}<br>
            <hr>
            <b>Directly Reaches:</b><br>
            • {connections_list}
        </div>
        """
        
        # Color hubs by how important they are
        color = 'red' if count > 4 else 'orange' if count > 2 else 'blue'

        folium.CircleMarker(
            location=[row['stop_lat'], row['stop_lon']],
            radius=count * 2, # Size reflects importance
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

    # 7. Save and Open
    os.makedirs('plots', exist_ok=True)
    m.save('plots/hub_explorer.html')
    print(f"✅ Success! {len(main_hubs)} hubs mapped.")
    print("👉 Open 'plots/hub_explorer.html' in your browser.")

if __name__ == "__main__":
    create_hub_explorer()