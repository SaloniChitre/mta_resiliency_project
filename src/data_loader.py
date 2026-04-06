import pandas as pd

def quick_clean():
    print("--- Midpoint Deliverable: Data Cleaning ---")
    try:
        # Load only the first 10,000 rows to save memory/space
        stops = pd.read_csv('data/raw/stops.txt')
        hubs = stops[stops['location_type'] == 1]
        
        # Save the processed file
        hubs.to_csv('data/processed/cleaned_hubs.csv', index=False)
        
        print(f"Success! Cleaned {len(hubs)} hubs.")
        print(hubs[['stop_name', 'stop_lat', 'stop_lon']].head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_clean()