import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

def plot_mta_graph():
    print("--- 🎨 Visualizing NYC Subway Digital Twin ---")
    
    # 1. Load your Nodes and Edges
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # 2. Initialize the Graph
    G = nx.Graph()
    
    # 3. Add Nodes with Positions (Lat/Lon)
    # We use longitude as X and latitude as Y
    pos = {}
    for _, row in hubs.iterrows():
        node_id = str(row['stop_id'])
        G.add_node(node_id, name=row['stop_name'])
        pos[node_id] = (row['stop_lon'], row['stop_lat'])
    
    # 4. Add Edges
    for _, row in edges.iterrows():
        u, v = str(row['source']), str(row['target'])
        if u in G and v in G:
            G.add_edge(u, v)

    # 5. Draw the Map
    plt.figure(figsize=(12, 16))
    
    nx.draw_networkx_nodes(G, pos, node_size=10, node_color='blue', alpha=0.6)
    nx.draw_networkx_edges(G, pos, width=0.5, edge_color='gray', alpha=0.4)
    
    plt.title("NYC Subway Network Topology (Digital Twin v1.0)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, linestyle='--', alpha=0.5)
    
    print("Saving map to 'outputs/subway_network_map.png'...")
    os.makedirs('outputs', exist_ok=True)
    plt.savefig('outputs/subway_network_map.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    import os
    plot_mta_graph()