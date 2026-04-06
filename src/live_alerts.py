import pandas as pd
import numpy as np
import sys
import os

def trigger_node_failure(node_x_id="635", flood_intensity=9.5):
    """
    node_x_id: The ID of the station you want to 'Break' (e.g., 635 for Atlantic Av)
    flood_intensity: The simulated rain hitting that specific node
    """
    print(f"\n" + "!"*60)
    print(f"🚨 CRITICAL TRIGGER ACTIVATED ON NODE: {node_x_id} 🚨")
    print("!"*60)

    # 1. Load the Infrastructure Graph
    try:
        hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
        edges = pd.read_csv('data/processed/weather_aware_edges.csv')
        
        # Ensure IDs are strings for matching
        hubs['stop_id'] = hubs['stop_id'].astype(str)
        edges['source'] = edges['source'].astype(str)
        edges['target'] = edges['target'].astype(str)
    except Exception as e:
        print(f"❌ Data Loading Error: {e}")
        return

    # 2. Identify Node X
    target_node = hubs[hubs['stop_id'] == node_x_id]
    if target_node.empty:
        print(f"❌ Error: Node {node_x_id} not found in the Digital Twin.")
        return
    
    node_name = target_node.iloc[0]['stop_name']
    print(f"📍 Location: {node_name}")
    print(f"🌊 Simulated Intensity: {flood_intensity} mm/hr")

    # 3. Find ALL Connected Nodes (The "Blast Radius")
    # We look for any edge where Node X is either the source or the target
    connections = edges[(edges['source'] == node_x_id) | (edges['target'] == node_x_id)]
    
    print(f"\n📢 GENERATING SUBSEQUENT ALERTS FOR CONNECTED INFRASTRUCTURE:")
    print("-" * 70)
    print(f"{'CONNECTED NODE':<30} | {'STATUS':<15} | {'ACTION REQUIRED'}")
    print("-" * 70)

    alert_list = []
    for _, edge in connections.iterrows():
        # Identify the "Neighbor" node
        neighbor_id = edge['target'] if edge['source'] == node_x_id else edge['source']
        neighbor_name = hubs[hubs['stop_id'] == neighbor_id]['stop_name'].values[0]
        
        # Risk Logic: If Node X is flooded, the connection is SEVERED
        status = "🔴 SEVERED"
        action = "EMERGENCY BRAKE / REROUTE"
        
        print(f"{neighbor_name:<30} | {status:<15} | {action}")
        alert_list.append(neighbor_id)

    print("-" * 70)
    print(f"✅ Total Subsequent Alerts Dispatched: {len(alert_list)}")
    print(f"🛡️  Digital Twin Recommendation: Isolate {node_name} and notify {len(alert_list)} neighbors.")

if __name__ == "__main__":
    # Test with Atlantic Av (635)
    # You can change this ID to any station from your cleaned_hubs.csv
    trigger_node_failure(node_x_id="635", flood_intensity=9.5)