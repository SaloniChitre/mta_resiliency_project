import pandas as pd
import numpy as np

def get_dynamic_reroute_strategy(main_hub, all_hubs, cascade_radius, is_critical):
    """
    Calculates the best bypass station and specific line actions 
    based on the current simulation state.
    """
    if not is_critical:
        return {
            "bypass_target": "Optimal",
            "j_mz_action": "Standard Headways",
            "g_line_action": "Standard Consist",
            "bus_bridge": False
        }

    # 1. Find the Primary Bypass: Nearest station OUTSIDE the cascade radius
    # We filter out nodes within the red circle to ensure the bypass is safe
    safe_candidates = all_hubs[all_hubs['dist_to_selected'] > cascade_radius].copy()
    
    if safe_candidates.empty:
        bypass_target = "System Shutdown"
    else:
        # Prioritize high-capacity hubs as bypass targets
        safe_candidates['score'] = safe_candidates['daily_ridership'] / (safe_candidates['dist_to_selected'] + 0.1)
        bypass_target = safe_candidates.nlargest(1, 'score').iloc[0]['stop_name']

    # 2. Logic-based Line Actions
    # If the hub is a high-ridership hub, we need more aggressive Consist/Headway changes
    is_high_load = main_hub['daily_ridership'] > 40000
    
    strategy = {
        "bypass_target": bypass_target,
        "j_mz_action": "Reduce headways to 3m" if is_high_load else "Reduce headways to 5m",
        "g_line_action": "Deploy 10-car sets" if is_high_load else "Deploy 8-car sets",
        "bus_bridge": True if is_high_load or main_hub['physical_risk_score'] > 0.7 else False
    }
    
    return strategy