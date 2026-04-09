import networkx as nx
import numpy as np

def build_mta_graph(df):
    """Initializes the NetworkX graph using the hubs dataframe."""
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_node(
            row['stop_name'], 
            lat=row['stop_lat'], 
            lon=row['stop_lon'],
            routes=row.get('routes', ['1']) 
        )
    
    stops = df['stop_name'].tolist()
    for i in range(len(stops) - 1):
        u, v = stops[i], stops[i+1]
        dist = np.sqrt((G.nodes[u]['lat'] - G.nodes[v]['lat'])**2 + 
                       (G.nodes[u]['lon'] - G.nodes[v]['lon'])**2)
        G.add_edge(u, v, distance=dist, weight=dist)
    return G

def get_agentic_path(G, start_node, target_node, intensity_map, selected_line="All"):
    """
    Finds the safest path. 
    Cost = Distance * (1 + Rainfall Probability * 8.0 Penalty)
    """
    active_G = G.copy()

    if selected_line != "All":
        nodes_to_remove = [n for n, d in active_G.nodes(data=True) 
                          if selected_line not in d.get('routes', [])]
        active_G.remove_nodes_from(nodes_to_remove)

    for u, v, d in active_G.edges(data=True):
        # We penalize the edge if the target node (v) is high risk
        node_risk = intensity_map.get(v, 0.0) 
        d['weight'] = d.get('distance', 1.0) * (1 + (node_risk * 8.0))

    try:
        return nx.shortest_path(active_G, source=start_node, target=target_node, weight='weight')
    except:
        return [start_node] # Fallback to avoid crash