import pandas as pd
import geopandas as gpd
from geodatasets import get_path
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os

def plot_real_world_map():
    print("--- 🗺️ Generating Real-World Context Map ---")
    
    # 1. Load Data
    try:
        hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
        edges = pd.read_csv('data/processed/network_edges.csv')
    except FileNotFoundError:
        print("❌ Error: CSV files not found!")
        return
    
    # 2. Load NYC Borough Boundaries
    path = get_path('nybb')
    nyc = gpd.read_file(path)
    nyc = nyc.to_crs(epsg=4326)

    # 3. Setup Plot
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Draw NYC Land
    nyc.plot(ax=ax, color='#f2f2f2', edgecolor='#bcbcbc', zorder=1)
    
    # 4. Draw the Tracks (Edges)
    coords = {str(row['stop_id']): (row['stop_lon'], row['stop_lat']) for _, row in hubs.iterrows()}
    for _, row in edges.iterrows():
        u, v = str(row['source']), str(row['target'])
        if u in coords and v in coords:
            ax.plot([coords[u][0], coords[v][0]], [coords[u][1], coords[v][1]], 
                     color='#3498db', linewidth=1.2, alpha=0.7, zorder=2)

    # 5. Draw the Stations (Nodes)
    ax.scatter(hubs['stop_lon'], hubs['stop_lat'], s=10, color='#e74c3c', alpha=0.8, zorder=3)
    
    # 6. Define and Add Legend (Fixed the scoping and syntax)
    legend_elements = [
        Line2D([0], [0], color='#3498db', lw=2, label='Subway Tracks (Edges)'),
        Line2D([0], [0], marker='o', color='w', label='Station Hubs (Nodes)',
               markerfacecolor='#e74c3c', markersize=8),
        plt.Rectangle((0, 0), 1, 1, fc="#f2f2f2", edgecolor='#bcbcbc', label='NYC Boroughs')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

    plt.title("NYC Resilience Digital Twin: Network vs. Geography", fontsize=16)
    plt.axis('off')
    
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/real_world_context.png', dpi=300, bbox_inches='tight')
    print("✅ Success! Check 'plots/real_world_context.png'")
    plt.show()

if __name__ == "__main__":
    plot_real_world_map()