import numpy as np
import pandas as pd

def run_cluster_monte_carlo(hub_data, neighbors, intensity, mitigation, load_mult, iterations=1000):
    """
    Generates unique failure probabilities for each node in the cluster.
    """
    base_capacity = 8.0 
    if mitigation:
        base_capacity *= 1.5
    
    # 1. Primary Hub Simulation (Gaussian distribution around selected intensity)
    rain_samples = np.random.normal(intensity, 1.0, iterations)
    # Ensure no negative rain
    rain_samples = np.maximum(rain_samples, 0)
    
    threshold = base_capacity / (1 + (load_mult - 1) * 0.3)
    primary_failures = rain_samples > threshold
    primary_prob = (np.sum(primary_failures) / iterations) * 100
    
    # 2. Neighbor Simulation with Spatial Variance
    neighbor_probs = {}
    for _, neighbor in neighbors.iterrows():
        # Each neighbor gets a unique intensity sample (spatial variance)
        n_intensity = intensity * np.random.uniform(0.7, 1.3)
        n_samples = np.random.normal(n_intensity, 1.2, iterations)
        n_samples = np.maximum(n_samples, 0)
        
        # Threshold adjusted by the node's specific physical risk score
        n_threshold = base_capacity * (1.0 - neighbor['physical_risk_score'])
        n_failures = n_samples > n_threshold
        neighbor_probs[neighbor['stop_name']] = (np.sum(n_failures) / iterations) * 100

    return {
        "failure_prob": primary_prob,
        "neighbor_probs": neighbor_probs, 
        "raw_data": pd.DataFrame({
            "Rain_Sample": rain_samples,
            "Failed": primary_failures
        })
    }