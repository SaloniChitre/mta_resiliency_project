import pandas as pd

# Load your newly cleaned data
hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
stops = pd.read_csv('data/raw/stops.txt')

# 'stop_id' in hubs (location_type 1) is the Parent ID. 
# We need to see how many unique 'Child' platforms each Hub has.
# More platforms usually means more intersecting lines.

child_counts = stops.groupby('parent_station').size().reset_index(name='connectivity_score')
top_hubs = hubs.merge(child_counts, left_on='stop_id', right_on='parent_station')

# Sort by connectivity
top_10 = top_hubs.sort_values(by='connectivity_score', ascending=False).head(10)

print("\n--- Midpoint Deliverable: Initial Modeling ---")
print("Top 10 Potential 'Super-Spreader' Hubs identified by Connectivity:")
print(top_10[['stop_name', 'connectivity_score']])