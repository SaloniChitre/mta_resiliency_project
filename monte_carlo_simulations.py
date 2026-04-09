import pandas as pd
import numpy as np

def run_cluster_monte_carlo(target_node, neighbor_nodes, intensity=4.0, mitigation=False, load_mult=1.0, iterations=500):
    """
    Simulates rainfall failure events with probabilistic neighbor cascading.
    """
    # Generate random storm scenarios using a Rayleigh distribution
    simulated_rain = np.random.rayleigh(scale=intensity, size=iterations)
    
    results = []
    
    # Mitigation (Pumps) reduces the 'effective' rain volume
    pump_efficiency = 0.65 if mitigation else 1.0
    
    for rain in simulated_rain:
        # 1. PRIMARY NODE LOGIC
        # Base health is 11.0 to provide a realistic buffer for NYC infrastructure
        base_health = 11.0
        structural_jitter = np.random.normal(0, 0.5)
        
        # Threshold drops as physical_risk_score and load_mult (event surge) increase
        resilience_threshold = (base_health - (target_node['physical_risk_score'] * 6.0)) / load_mult
        
        effective_rain = rain * pump_efficiency
        is_failed = effective_rain >= (resilience_threshold + structural_jitter)
        
        # 2. NEIGHBOR CASCADE LOGIC (Gradual Failure)
        # Instead of 0 or 18, we calculate how many individual neighbors fail.
        neighbor_fails = 0
        if is_failed:
            # How far beyond the threshold did the rain go?
            excess_severity = effective_rain - resilience_threshold
            
            # Probability of a neighbor failing increases with rain intensity
            # If rain is just over the limit, maybe 10% fail. If it's a flood, 90% fail.
            fail_chance = min(0.95, (excess_severity / 5.0)) 
            
            for _ in range(len(neighbor_nodes)):
                # Each neighbor gets its own random roll
                if np.random.random() < fail_chance:
                    neighbor_fails += 1
        
        results.append({
            "rainfall": rain,
            "failed": is_failed,
            "neighbors_impacted": neighbor_fails
        })
    
    df = pd.DataFrame(results)
    
    # Calculate global metrics for the dashboard KPIs
    total_neighbors = max(len(neighbor_nodes), 1)
    failure_prob = (df['failed'].sum() / iterations) * 100
    cascade_risk = (df['neighbors_impacted'].sum() / (iterations * total_neighbors)) * 100
    
    return {
        "failure_prob": failure_prob,
        "cascade_risk": cascade_risk,
        "raw_data": df
    }