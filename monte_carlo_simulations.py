import pandas as pd
import numpy as np

def run_cluster_monte_carlo(target_node, neighbor_nodes, iterations=500):
    """
    Simulates random rainfall events for a specific station cluster.
    """
    # Generate random rainfall using a Rayleigh distribution (common for storm modeling)
    simulated_rain = np.random.rayleigh(scale=3.5, size=iterations)
    
    results = []
    for rain in simulated_rain:
        # A node fails if rain exceeds its risk-adjusted threshold
        threshold = 4.8 - (target_node['physical_risk_score'] * 1.8)
        is_failed = rain >= threshold
        
        # Count neighbor impacts (neighbors fail easier if primary hub is inundated)
        neighbor_fails = len(neighbor_nodes) if rain > 5.5 else 0
        
        results.append({
            "rainfall": rain,
            "failed": is_failed,
            "neighbors_impacted": neighbor_fails
        })
    
    df = pd.DataFrame(results)
    
    return {
        "failure_prob": (df['failed'].sum() / iterations) * 100,
        "cascade_risk": (df['neighbors_impacted'].sum() / (iterations * max(len(neighbor_nodes), 1))) * 100,
        "raw_data": df
    }