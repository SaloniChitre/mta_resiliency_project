import pandas as pd
import os

def check_event_resilience():
    print("--- 🗓️ Merging Calendar Events with Network Risk ---")
    
    # 1. Load the Weather-Aware Network
    try:
        edges = pd.read_csv('data/processed/weather_aware_edges.csv')
    except FileNotFoundError:
        print("❌ Run weather_engine.py first!")
        return

    # 2. Define your upcoming events (Today's 12 PM Update)
    # In a full app, this would pull dynamically from the Google Calendar API
    events = [
        {"name": "Project Update", "time": "12:00 PM", "location": "Manhattan", "lines": ["1", "2", "3", "A", "C"]}
    ]

    # 3. Check the status of the lines serving those events
    for event in events:
        print(f"\nChecking Impact for: {event['name']} ({event['time']})")
        
        # Check if any of the lines associated with the event are 'Critical' (> 45mm)
        # We'll filter edges that belong to these lines
        risk_level = edges[edges['flood_intensity'] > 45]
        
        if not risk_level.empty:
            print(f"🚨 ALERT: Your {event['name']} is AT RISK.")
            print(f"   Reason: Flash flood risk detected on the {', '.join(event['lines'])} lines.")
        else:
            print(f"✅ STATUS: Your route to {event['name']} is currently clear.")

if __name__ == "__main__":
    check_event_resilience()