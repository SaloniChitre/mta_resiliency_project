import pandas as pd
import os

def build_transit_graph():
    print("\n--- Building MTA Network Graph ---")
    
    # 1. Load Data
    stops = pd.read_csv('data/raw/stops.txt')
    stop_times = pd.read_csv('data/raw/stop_times.txt')
    
    # 2. Map every child platform to its Parent Hub
    # This is CRITICAL so edges connect Hub-to-Hub
    stop_to_parent = stops.set_index('stop_id')['parent_station'].to_dict()
    
    # 3. Get sequences of stops for each trip
    print("Processing trip sequences...")
    stop_times = stop_times.sort_values(['trip_id', 'stop_sequence'])
    
    edges = []
    # Group by trip to find which station follows which
    for trip_id, group in stop_times.groupby('trip_id'):
        nodes = group['stop_id'].tolist()
        for i in range(len(nodes) - 1):
            # Get the Parent ID for the current and next stop
            u = stop_to_parent.get(nodes[i], nodes[i])
            v = stop_to_parent.get(nodes[i+1], nodes[i+1])
            
            # Only add the edge if it's a move between different hubs
            if u != v and pd.notna(u) and pd.notna(v):
                edges.append({'source': u, 'target': v})
    
    # 4. Save the unique edges
    edge_df = pd.DataFrame(edges).drop_duplicates()
    edge_df.to_csv('data/processed/network_edges.csv', index=False)
    
    print(f"✅ Success! Generated {len(edge_df)} unique hub-to-hub connections.")
    print(edge_df.head())

if __name__ == "__main__":
    build_transit_graph()