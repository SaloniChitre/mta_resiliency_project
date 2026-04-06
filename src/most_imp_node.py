import pandas as pd
import networkx as nx

def find_system_bottlenecks():
    print("--- 🔬 Finding Structural Bottlenecks ---")
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    G = nx.Graph()
    for _, row in edges.iterrows():
        G.add_edge(str(row['source']), str(row['target']))

    # Find "Bridges" - edges that, if removed, increase the number of isolated clusters
    bridges = list(nx.bridges(G))
    
    print(f"⚠️ Critical Vulnerability Found: {len(bridges)} 'Single-Point-of-Failure' tracks.")
    
    # Let's see which stations these connect
    id_to_name = pd.Series(hubs.stop_name.values, index=hubs.stop_id.astype(str)).to_dict()
    
    for u, v in bridges[:10]: # Just show the top 10
        print(f" - Critical Link: {id_to_name.get(u)} <-> {id_to_name.get(v)}")

if __name__ == "__main__":
    find_system_bottlenecks()