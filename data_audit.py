import pandas as pd
import os

def run_network_audit():
    print("--- 🔍 MTA Data Deep-Dive Audit ---")
    
    # 1. Load the raw files
    stops = pd.read_csv('data/raw/stops.txt')
    stop_times = pd.read_csv('data/raw/stop_times.txt')
    trips = pd.read_csv('data/raw/trips.txt')
    
    # 2. Map Platforms to Hubs
    # We create a dictionary to quickly look up which Hub a Platform belongs to
    stop_to_hub = stops.set_index('stop_id')['parent_station'].to_dict()
    hub_names = stops[stops['location_type'] == 1].set_index('stop_id')['stop_name'].to_dict()

    # 3. Calculate "Route Diversity" (How many different trains at each Hub)
    print("Calculating Route Diversity per Hub...")
    # Join stop_times and trips to get the Route ID (A, C, 1, etc.)
    merged = stop_times.merge(trips[['trip_id', 'route_id']], on='trip_id')
    
    # Map the stop_id in stop_times to its Parent Hub
    merged['hub_id'] = merged['stop_id'].map(stop_to_hub)
    
    # Group by Hub and count UNIQUE Route IDs
    route_counts = merged.groupby('hub_id')['route_id'].nunique().sort_values(ascending=False)

    # 4. Display the results
    print("\n🏆 Top 10 Hubs by Route Diversity (True Connectivity):")
    for hub_id, count in route_counts.head(10).items():
        name = hub_names.get(hub_id, "Unknown Hub")
        print(f"{name.ljust(30)} | {count} Unique Lines")

    # 5. Data Integrity Check
    total_hubs = len(stops[stops['location_type'] == 1])
    hubs_with_service = merged['hub_id'].nunique()
    
    print("\n--- 📊 Integrity Summary ---")
    print(f"Total Hubs Defined: {total_hubs}")
    print(f"Hubs with Active Service: {hubs_with_service}")
    
    if total_hubs > hubs_with_service:
        print(f"⚠️ Warning: {total_hubs - hubs_with_service} hubs have NO train service listed in stop_times!")

if __name__ == "__main__":
    run_network_audit()