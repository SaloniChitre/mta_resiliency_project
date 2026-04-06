import pandas as pd
import sys
import os

# Path Fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from weather_service import MockWeatherService

def run_automated_presentation_demo(threshold=4.0):
    print("\n" + "="*70)
    print("📈 MTA RESILIENCY PROJECT: AUTOMATED RISK ASSESSMENT DEMO")
    print("="*70)

    weather_api = MockWeatherService()
    hubs = pd.read_csv('data/processed/cleaned_hubs.csv')
    edges = pd.read_csv('data/processed/weather_aware_edges.csv')
    name_lookup = dict(zip(hubs['stop_id'].astype(str), hubs['stop_name']))

    # 1. SCAN AND RANK
    results = []
    for _, station in hubs.iterrows():
        s_id = str(station['stop_id'])
        rain = weather_api.get_rainfall(station['stop_lat'], station['stop_lon'])
        if rain >= threshold:
            impact = len(edges[(edges['source'].astype(str) == s_id) | (edges['target'].astype(str) == s_id)])
            results.append({"id": s_id, "name": station['stop_name'], "rain": rain, "impact": impact, "score": rain * impact})

    if not results:
        print("🟢 SYSTEM STATUS: Normal. No alerts triggered.")
        return

    df_results = pd.DataFrame(results).sort_values(by='score', ascending=False)
    
    # 2. VULNERABILITY LEADERBOARD
    print(f"\n📊 TOP 5 VULNERABILITY RANKING (AUTOMATED):")
    print("-" * 70)
    for i, (idx, row) in enumerate(df_results.head(5).iterrows()):
        print(f"{i+1}. {row['name']:<25} | Rain: {row['rain']}mm | Score: {row['score']:.1f}")
    
    # 3. TRIGGER AUTOMATED ALERTS
    top_hub = df_results.iloc[0]
    print(f"\n📢 TRIGGERING CASCADE ALERTS FOR: {top_hub['name']}")
    print("-" * 70)
    
    neighbors = edges[(edges['source'].astype(str) == top_hub['id']) | (edges['target'].astype(str) == top_hub['id'])]
    for _, edge in neighbors.iterrows():
        n_id = str(edge['target']) if str(edge['source']) == top_hub['id'] else str(edge['source'])
        print(f"⚠️  ALERT DISPATCHED: Sector {top_hub['name']} -> {name_lookup.get(n_id, n_id)} (EVACUATE/REROUTE)")

    print("\n✅ End Product Delivery: Real-Time Assessment Dashboard Complete.")

if __name__ == "__main__":
    run_automated_presentation_demo(threshold=4.0)