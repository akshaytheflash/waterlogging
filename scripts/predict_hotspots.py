import pandas as pd
import numpy as np
import xgboost as xgb
import psycopg2
import requests
from sklearn.cluster import DBSCAN
import os
import json

# Configuration
DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
MODEL_PATH = os.path.join("models", "waterlogging_xgb.json")
DELHI_BOUNDS = {'min_lat': 28.40, 'max_lat': 28.90, 'min_lng': 76.80, 'max_lng': 77.35}

def get_live_weather():
    """Fetch live accumulated rain for Delhi from Open-Meteo"""
    # Simply using a central point for Delhi for now
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 28.61,
        "longitude": 77.20,
        "hourly": "rain",
        "past_days": 1
    }
    try:
        r = requests.get(url, params=params).json()
        hourly = r.get('hourly', {})
        rain = hourly.get('rain', [])
        
        # Calculate last 1h and 24h rain
        # This is a simplification. In prod we match timestamps exactly.
        rain_1h = rain[-1] if rain else 0
        rain_24h = sum(rain[-24:]) if len(rain) >= 24 else sum(rain)
        
        return rain_1h, rain_24h
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return 0, 0

def generate_grid():
    """Generate a grid of points over Delhi"""
    lats = np.linspace(DELHI_BOUNDS['min_lat'], DELHI_BOUNDS['max_lat'], num=50)
    lngs = np.linspace(DELHI_BOUNDS['min_lng'], DELHI_BOUNDS['max_lng'], num=50)
    print(f"DEBUG: Grid step lat={(lats[1]-lats[0]):.4f}, lng={(lngs[1]-lngs[0]):.4f}")
    
    grid = []
    for lat in lats:
        for lng in lngs:
            grid.append({
                'lat': lat,
                'lng': lng,
                'elevation_rel': np.random.normal(5, 2), # Mock elevation data
                'drain_dist': np.random.exponential(500) # Mock infra data
            })
    return pd.DataFrame(grid)

def update_hotspots():
    # 1. Load Model
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Run train_model.py first.")
        return

    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    
    # 2. Get Weather
    rain_1h, rain_24h = get_live_weather()
    print(f"Current Weather: 1h Rain={rain_1h}mm, 24h Rain={rain_24h}mm")
    
    # 3. Generate Grid & Features
    grid_df = generate_grid()
    grid_df['rain_1h'] = rain_1h
    grid_df['rain_24h'] = rain_24h
    
    # 4. Predict Risk
    X = grid_df[['rain_1h', 'rain_24h', 'elevation_rel', 'drain_dist']]
    probs = model.predict_proba(X)[:, 1] # Probability of class 1
    
    print(f"Max detected risk probability: {probs.max():.4f}")
    
    # Filter high risk
    high_risk_df = grid_df[probs > 0.7].copy()
    
    if high_risk_df.empty:
        print("No high risk areas detected.")
        clear_ai_hotspots()
        return

    print(f"Detected {len(high_risk_df)} high-risk points.")

    # 5. Cluster (DBSCAN) to form Hotspots
    # Convert lat/lng to radians for haversine metric if needed, but euclidean is fine for small area approx
    # EPS=0.012 (approx 1.2km).
    # Grid step is ~0.01. EPS must be > Step to connect neighbors.
    coords = high_risk_df[['lat', 'lng']].values
    print(f"Clustering {len(coords)} points...")
    db = DBSCAN(eps=0.012, min_samples=3).fit(coords)
    
    labels = db.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"Formed {n_clusters} hotspots from {len(set(labels))} unique labels (including noise).")
    if n_clusters == 0 and len(coords) > 0:
        print("DEBUG: All points classified as noise (-1). Try increasing EPS or reducing min_samples.")
        print(f"Sample labels: {labels[:20]}")
    
    hotspots = []
    for label in set(labels):
        if label == -1: continue # Noise
        
        cluster_points = coords[labels == label]
        centroid = cluster_points.mean(axis=0)
        
        # Calculate Radius (Furthest point from centroid)
        # 1 degree Lat ~= 111km. Simple Euclidean approx is okay for small scale.
        distances = np.sqrt(((cluster_points - centroid)**2).sum(axis=1))
        max_dist_deg = distances.max()
        radius_meters = int(max_dist_deg * 111000) # Convert degrees to meters
        
        # Ensure minimum visibility (e.g. 200m) and add buffer
        radius_meters = max(200, radius_meters + 100)

        hotspots.append({
            'name': f"AI-Detected Likely Hotspot #{label+1}",
            'lat': centroid[0],
            'lng': centroid[1],
            'radius': radius_meters,
            'risk': 'High',
            'desc': f"High probability of waterlogging due to {round(rain_24h, 1)}mm rain."
        })
        
    # 6. Update Database
    save_hotspots_to_db(hotspots)

def clear_ai_hotspots():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM hotspots WHERE source = 'ai_predicted'")
    conn.commit()
    conn.close()
    print("Cleared old AI hotspots.")

def save_hotspots_to_db(hotspots):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Clear old AI predictions
        cur.execute("DELETE FROM hotspots WHERE source = 'ai_predicted'")
        
        for h in hotspots:
            cur.execute("""
                INSERT INTO hotspots (name, description, severity, lat, lng, source, radius)
                VALUES (%s, %s, %s, %s, %s, 'ai_predicted', %s)
            """, (h['name'], h['desc'], h['risk'], float(h['lat']), float(h['lng']), int(h['radius'])))
            
        conn.commit()
        print("Database updated successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    import sys
    
    # helper to find value after a flag
    def get_arg(flag, default):
        try:
            idx = sys.argv.index(flag)
            return float(sys.argv[idx+1])
        except (ValueError, IndexError):
            return default

    if "--simulate" in sys.argv:
        # Default: 150mm (Heavy rain) if not specified
        custom_rain = get_arg("--rain", 150.0)
        
        print(f"SIMULATION MODE: Injecting {custom_rain}mm rain data...")
        
        # Monkey patch get_live_weather for this run
        # Returns (last_hour_rain, last_24h_rain)
        # We assume last hour is ~1/6th of total for simulation
        get_live_weather = lambda: (custom_rain / 6.0, custom_rain) 
        
    update_hotspots()
