import requests
import json
from datetime import datetime

# Open-Meteo API Endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"

# Delhi Coordinates (Center)
LAT = 28.6139
LNG = 77.2090

def fetch_weather_forecast():
    """
    Fetches hourly rain forecast for the next 24 hours for Delhi.
    """
    params = {
        "latitude": LAT,
        "longitude": LNG,
        "hourly": "rain",
        "timezone": "auto",
        "forecast_days": 1
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        rain = hourly.get("rain", [])
        
        print(f"\n--- Weather Forecast for Delhi ({LAT}, {LNG}) ---")
        print(f"{'Time':<25} | {'Rain (mm)':<10}")
        print("-" * 40)
        
        total_rain = 0
        for t, r in zip(times, rain):
            # Parse time to be more readable
            dt = datetime.fromisoformat(t)
            print(f"{dt.strftime('%Y-%m-%d %H:%M'):<25} | {r:<10} mm")
            total_rain += r
            
        print("-" * 40)
        print(f"Total Expected Rain (24h): {round(total_rain, 2)} mm")
        
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

if __name__ == "__main__":
    fetch_weather_forecast()
