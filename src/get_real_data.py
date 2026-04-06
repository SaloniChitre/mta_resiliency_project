import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import os

def fetch_nyc_weather():
    print("--- 📡 Fetching Real-Time NOAA/Open-Meteo Data ---")
    
    # Setup API client with cache
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Coordinates for NYC Center (Manhattan/Jersey City area)
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "hourly": "precipitation",
        "timezone": "America/New_York",
        "past_days": 1 
    }
    
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        response = responses[0]

        # Extract hourly precipitation
        hourly = response.Hourly()
        precipitation = hourly.Variables(0).ValuesAsNumpy()
        
        # We take the peak hourly rainfall for our "Stress Test"
        peak_rain = float(max(precipitation))
        
        # Create a spatial distribution (NYC is a grid, so we simulate slight variance)
        data = [
            [40.7128, -74.0060, peak_rain],       # Manhattan/Jersey City
            [40.8500, -73.9000, peak_rain * 0.85], # Bronx
            [40.6500, -73.9500, peak_rain * 1.1],  # Brooklyn (often gets more rain)
            [40.7500, -73.8000, peak_rain * 0.9]   # Queens
        ]
        
        df = pd.DataFrame(data, columns=['LATITUDE', 'LONGITUDE', 'PRCP'])
        
        os.makedirs('data/raw', exist_ok=True)
        df.to_csv('data/raw/noaa_nyc_2026.csv', index=False)
        
        print(f"✅ Success! Peak rain detected: {peak_rain:.2f} mm")
        
    except Exception as e:
        print(f"❌ Error fetching weather: {e}")

if __name__ == "__main__":
    fetch_nyc_weather()