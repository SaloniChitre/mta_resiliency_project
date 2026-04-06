import pandas as pd
import folium
import networkx as nx
import os

def create_bottleneck_map():
    print("--- 🔬 Generating SPOF Bottleneck Map ---")
    
    # 1. Load Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # Mapping for lookups
    coords = {str(row['stop_id']): [row['stop_lat'], row['stop_lon']] for _, row in hubs.iterrows()}
    names = {str(row['stop_id']): row['stop_name'] for _, row in hubs.iterrows()}

    # 2. Build the Network Graph and find "Bridges" (Single Points of Failure)
    G = nx.Graph()
    for _, row in edges.iterrows():
        G.add_edge(str(row['source']), str(row['target']))
        
    # Find Bridges (mathematical term for SPOF edges)
    bridges = set(nx.bridges(G))
    print(f"⚠️ Critical Vulnerability Found: {len(bridges)} tracks have ZERO redundancy.")

    # 3. Initialize Map (Cleaner base)
    m = folium.Map(location=[40.7300, -73.9500], zoom_start=12, tiles='cartodbpositron')

    # 4. Draw ALL standard tracks in faint blue (the background)
    for _, row in edges.iterrows():
        u, v = str(row['source']), str(row['target'])
        if u in coords and v in coords:
            # We will color normal tracks light blue and make them slightly transparent
            is_spof = (u, v) in bridges or (v, u) in bridges
            if not is_spof:
                folium.PolyLine(
                    locations=[coords[u], coords[v]],
                    color='#3498db', weight=2, opacity=0.3
                ).add_to(m)

    # 5. Overlay ONLY the SPOFs in thick red (the bottlenecks)
    for u, v in bridges:
        if u in coords and v in coords:
            # Add the bottleneck layer with a glowing effect
            folium.PolyLine(
                locations=[coords[u], coords[v]],
                color='#e74c3c', weight=6, opacity=1.0, # Thick and bright
                tooltip=f"CRITICAL SPOF: {names[u]} ↔ {names[v]}<br>Impact: Network Fragmentation"
            ).add_to(m)

    # 6. Add Station Points (Small dots)
    for _, row in hubs.iterrows():
        folium.CircleMarker(
            location=[row['stop_lat'], row['stop_lon']],
            radius=1.5, color='black', fill=True, fill_opacity=0.3
        ).add_to(m)

    # 7. Save and Open
    os.makedirs('plots', exist_ok=True)
    m.save('plots/spof_bottleneck_map.html')
    print("✅ Bottleneck map saved to 'plots/spof_bottleneck_map.html'")
    print("👉 Zoom in to see the 'Single Points of Failure' in thick red.")

if __name__ == "__main__":
    create_bottleneck_map()