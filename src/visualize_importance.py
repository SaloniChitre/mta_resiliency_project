import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

def plot_importance_map():
    print("--- 🔥 Generating Station Importance Heatmap ---")
    
    # 1. Load Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # 2. Build Graph
    G = nx.Graph()
    pos = {}
    for _, row in hubs.iterrows():
        node_id = str(row['stop_id'])
        G.add_node(node_id, name=row['stop_name'])
        pos[node_id] = (row['stop_lon'], row['stop_lat'])
    
    for _, row in edges.iterrows():
        G.add_edge(str(row['source']), str(row['target']))

    # 3. Calculate Degree Centrality
    # This gives us a score for every station
    degrees = dict(G.degree())
    
    # 4. Plotting
    plt.figure(figsize=(12, 16))
    
    # Draw Edges in faint gray
    nx.draw_networkx_edges(G, pos, width=0.5, edge_color='lightgray', alpha=0.3)
    
    # Draw Nodes: Size and Color based on Degree
    nodes = nx.draw_networkx_nodes(
        G, pos, 
        node_size=[v * 15 for v in degrees.values()], # Bigger degree = Bigger dot
        node_color=list(degrees.values()),            # Color by importance
        cmap=plt.cm.YlOrRd,                           # Yellow to Red gradient
        alpha=0.8
    )
    
    plt.colorbar(nodes, label='Number of Connections (Degree)')
    plt.title("MTA Network Vulnerability: Hub Centrality Analysis")
    plt.axis('off')
    
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/station_importance.png', dpi=300)
    print("✅ Heatmap saved to 'plots/station_importance.png'")
    plt.show()

if __name__ == "__main__":
    plot_importance_map()