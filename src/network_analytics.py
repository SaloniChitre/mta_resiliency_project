import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_analytics():
    print("--- 📊 Generating Network Analytics Dashboard ---")
    
    # 1. Load Data
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/network_edges.csv')
    
    # 2. Build Graph
    G = nx.Graph()
    for _, row in edges.iterrows():
        G.add_edge(str(row['source']), str(row['target']))

    # 3. Visualization 1: Adjacency Matrix
    plt.figure(figsize=(10, 10))
    adj_matrix = nx.to_numpy_array(G)
    plt.imshow(adj_matrix, cmap='Greys', interpolation='none')
    plt.title("NYC Subway Adjacency Matrix (Network DNA)")
    plt.xlabel("Station Index")
    plt.ylabel("Station Index")
    
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/adjacency_matrix.png', dpi=300)
    print("✅ Adjacency Matrix saved.")

    # 4. Visualization 2: Degree Distribution (Risk Profile)
    plt.figure(figsize=(10, 6))
    degrees = [d for n, d in G.degree()]
    
    sns.histplot(degrees, bins=range(1, 10), kde=False, color='skyblue', edgecolor='black')
    plt.title("MTA Connectivity Profile: How many connections per station?")
    plt.xlabel("Number of Connections (Degree)")
    plt.ylabel("Number of Stations")
    plt.xticks(range(1, 10))
    
    plt.savefig('plots/degree_distribution.png', dpi=300)
    print("✅ Degree Distribution Histogram saved.")
    plt.show()

if __name__ == "__main__":
    generate_analytics()