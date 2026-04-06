import numpy as np

class MockWeatherService:
    def __init__(self):
        # We simulate a "Storm Center" at these coordinates (Brooklyn area)
        self.storm_center = [40.6841, -73.9785] 
        self.storm_intensity = 8.5 # Max rain in mm/hr at the center
        self.storm_radius = 0.05 # How far the rain spreads (in lat/lon degrees)

    def get_live_rainfall(self, lat, lon):
        # Calculate distance from the station to the storm center
        distance = np.sqrt((lat - self.storm_center[0])**2 + (lon - self.storm_center[1])**2)
        
        # If the station is inside the storm radius, it gets heavy rain
        if distance < self.storm_radius:
            # Linear decay: further from center = less rain
            rain = self.storm_intensity * (1 - (distance / self.storm_radius))
            return round(rain, 2)
        
        # Outside the storm, it's just a light drizzle
        return round(np.random.uniform(0, 1.5), 2)