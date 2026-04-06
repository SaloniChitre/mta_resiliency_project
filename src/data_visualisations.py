import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import os

def generate_meaningful_analytics():
    print("--- 📊 Generating Systemic Resiliency Analytics ---")
    
    # Ensure plots folder exists
    if not os.path.exists('plots'): os.makedirs('plots')
    
    # 1. Load Data
    try:
        edges = pd.read_csv('data/processed/weather_aware_edges.csv')
        hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    except Exception as e:
        print(f"❌ File Error: {e}")
        return

    # 2. Build the Network Graph
    G = nx.Graph()
    for _, row in edges.iterrows():
        G.add_edge(str(row['source']), str(row['target']), weight=1.0)
    
    # 3. Calculate Network Metrics
    # Degree (How many connections)
    degree_df = pd.DataFrame(list(G.degree()), columns=['stop_id', 'Degree'])
    
    # Eigenvector Centrality (How 'important' your neighbors are)
    # This identifies the real "Super-Hubs"
    centrality = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
    centrality_df = pd.DataFrame(list(centrality.items()), columns=['stop_id', 'Eigenvector Centrality'])
    
    # Closeness Centrality (How 'central' you are to the whole system)
    closeness = nx.closeness_centrality(G)
    closeness_df = pd.DataFrame(list(closeness.items()), columns=['stop_id', 'Closeness Centrality'])
    
    # 4. Calculate Risk per Station (Avg intensity of touching tracks)
    risk_u = edges[['source', 'flood_intensity']].rename(columns={'source': 'stop_id'})
    risk_v = edges[['target', 'flood_intensity']].rename(columns={'target': 'stop_id'})
    station_risk = pd.concat([risk_u, risk_v]).groupby('stop_id').mean().reset_index()
    station_risk = station_risk.rename(columns={'flood_intensity': 'Flood Risk (mm)'})
    
    # 5. Merge All Metrics
    metrics_df = pd.merge(degree_df, centrality_df, on='stop_id')
    metrics_df = pd.merge(metrics_df, closeness_df, on='stop_id')
    metrics_df = pd.merge(metrics_df, station_risk, on='stop_id')
    metrics_df = pd.merge(metrics_df, hubs[['stop_id', 'stop_name']], on='stop_id')

    # --- PLOT 1: Eigenvector Centrality vs. Flood Risk (Relational) ---
    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    
    # This plot identifies the "Vulnerable Super-Hubs"
    sns.regplot(data=metrics_df, x='Eigenvector Centrality', y='Flood Risk (mm)', 
                scatter_kws={'alpha':0.4, 's':100, 'color':'#2980b9'}, 
                line_kws={'color':'#c0392b', 'lw':2})

    # Label the top 10 most central hubs
    top_hubs = metrics_df.sort_values(by='Eigenvector Centrality', ascending=False).head(10)
    for i, row in top_hubs.iterrows():
        plt.text(row['Eigenvector Centrality'] + 0.01, row['Flood Risk (mm)'], 
                 row['stop_name'], fontsize=9, fontweight='bold', alpha=0.9)

    plt.title('MTA Digital Twin: Hub Centrality vs. Flood Exposure', fontsize=14)
    plt.xlabel('Hub Importance (Eigenvector Centrality)', fontsize=11)
    plt.ylabel('Average Flood Exposure (mm/hr)', fontsize=11)
    plt.savefig('plots/meaningful_correlation.png', dpi=300, bbox_inches='tight')
    print("✅ Success: 'plots/meaningful_correlation.png' generated.")
    
    # --- PLOT 2: The Correlation Heatmap (Statistical) ---
    plt.figure(figsize=(8, 6))
    sns.set_style("white")
    
    # Select only the relevant numerical metrics
    corr_matrix = metrics_df[['Degree', 'Eigenvector Centrality', 'Closeness Centrality', 'Flood Risk (mm)']].corr()
    
    # Create the heatmap
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1, linewidths=0.5)
    plt.title('Systemic Resiliency: Variable Correlation Matrix', fontsize=13)
    plt.xticks(rotation=45, ha='right') # Rotate labels for readability
    plt.savefig('plots/resiliency_heatmap.png', dpi=300, bbox_inches='tight')
    print("✅ Success: 'plots/resiliency_heatmap.png' generated.")
    
    # 6. Report the critical metric
    flood_corr = corr_matrix['Flood Risk (mm)']['Eigenvector Centrality']
    print(f"📈 Correlation (Centrality ↔ Flood): {flood_corr:.2f}")

if __name__ == "__main__":
    generate_meaningful_analytics()