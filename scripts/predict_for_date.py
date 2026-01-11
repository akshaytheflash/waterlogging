"""
Date-based Waterlogging Prediction Script
Generates predictions for specific dates using the trained ensemble model
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import json
import psycopg2
from dotenv import load_dotenv
from sklearn.cluster import DBSCAN
import requests

load_dotenv()

# Directories
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
DATABASE_URL = os.getenv('DATABASE_URL')

class DateBasedPredictor:
    """Predict waterlogging hotspots for a specific date"""
    
    def __init__(self):
        self.model_data = None
        self.load_model()
    
    def load_model(self):
        """Load trained model"""
        model_file = os.path.join(MODELS_DIR, 'waterlogging_advanced_v2.pkl')
        
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        with open(model_file, 'rb') as f:
            self.model_data = pickle.load(f)
        
        print(f"✅ Loaded model version: {self.model_data['model_version']}")
    
    def get_rainfall_for_date(self, target_date):
        """Get rainfall data for a specific date"""
        # Try to get from database first
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT rainfall_24h, temperature_c, humidity_percent
                FROM historical_rainfall
                WHERE record_date = %s
                LIMIT 1
            """, (target_date,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                return {
                    'rainfall_24h': float(result[0]),
                    'temperature': float(result[1]) if result[1] else 30.0,
                    'humidity': int(result[2]) if result[2] else 70
                }
        except Exception as e:
            print(f"   ⚠️  Could not fetch from database: {e}")
        
        # If not in database, use Open-Meteo API for historical/forecast data
        try:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            
            # Delhi coordinates
            lat, lng = 28.6139, 77.2090
            
            # Determine if historical or forecast
            today = datetime.now().date()
            target_date_obj = date_obj.date()
            
            if target_date_obj <= today:
                # Historical data
                url = f"https://archive-api.open-meteo.com/v1/archive"
                params = {
                    'latitude': lat,
                    'longitude': lng,
                    'start_date': target_date,
                    'end_date': target_date,
                    'daily': 'precipitation_sum,temperature_2m_max,relative_humidity_2m_max'
                }
            else:
                # Forecast data
                url = f"https://api.open-meteo.com/v1/forecast"
                params = {
                    'latitude': lat,
                    'longitude': lng,
                    'daily': 'precipitation_sum,temperature_2m_max,relative_humidity_2m_max',
                    'forecast_days': 16
                }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'daily' in data:
                idx = 0 if target_date_obj <= today else (target_date_obj - today).days
                
                return {
                    'rainfall_24h': data['daily']['precipitation_sum'][idx] or 0,
                    'temperature': data['daily']['temperature_2m_max'][idx] or 30.0,
                    'humidity': data['daily']['relative_humidity_2m_max'][idx] or 70
                }
        except Exception as e:
            print(f"   ⚠️  Could not fetch from API: {e}")
        
        # Fallback: Use seasonal averages
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        month = date_obj.month
        
        # Monsoon season (June-September) has higher rainfall
        if 6 <= month <= 9:
            rainfall = np.random.uniform(40, 80)
        else:
            rainfall = np.random.uniform(0, 20)
        
        return {
            'rainfall_24h': rainfall,
            'temperature': 30.0,
            'humidity': 70
        }
    
    def create_prediction_grid(self, target_date, rainfall_data):
        """Create a grid of points across Delhi for prediction"""
        # Delhi bounding box
        lat_min, lat_max = 28.4, 28.9
        lng_min, lng_max = 76.8, 77.4
        
        # Create grid (100m resolution = ~0.001 degrees)
        grid_size = 0.01  # ~1km resolution for faster computation
        
        lats = np.arange(lat_min, lat_max, grid_size)
        lngs = np.arange(lng_min, lng_max, grid_size)
        
        grid_points = []
        for lat in lats:
            for lng in lngs:
                grid_points.append({'lat': lat, 'lng': lng})
        
        df = pd.DataFrame(grid_points)
        
        # Add date and rainfall
        df['date'] = target_date
        df['rainfall_24h'] = rainfall_data['rainfall_24h']
        
        # Create features (same as training)
        df = self.create_features(df)
        
        return df
    
    def create_features(self, df):
        """Create features for prediction (same as training)"""
        df['date'] = pd.to_datetime(df['date'])
        
        # Temporal features
        df['day_of_year'] = df['date'].dt.dayofyear
        df['month'] = df['date'].dt.month
        df['is_monsoon'] = ((df['month'] >= 6) & (df['month'] <= 9)).astype(int)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Spatial features
        high_risk_zones = [
            (28.6330, 77.2285), (28.6304, 77.2425),
            (28.5910, 77.1610), (28.6139, 76.9830)
        ]
        
        def min_distance_to_risk_zone(row):
            lat, lng = row['lat'], row['lng']
            distances = [
                np.sqrt((lat - risk_lat)**2 + (lng - risk_lng)**2) * 111
                for risk_lat, risk_lng in high_risk_zones
            ]
            return min(distances)
        
        df['min_dist_to_risk_zone_km'] = df.apply(min_distance_to_risk_zone, axis=1)
        df['elevation_proxy'] = 28.7 - df['lat']
        
        # Rainfall features
        df['rainfall_squared'] = df['rainfall_24h'] ** 2
        df['rainfall_log'] = np.log1p(df['rainfall_24h'])
        df['rainfall_intensity_num'] = pd.cut(
            df['rainfall_24h'],
            bins=[0, 15, 35, 65, 115, 1000],
            labels=[1, 2, 3, 4, 5]
        ).astype(float)
        
        return df
    
    def predict_for_date(self, target_date):
        """Generate predictions for a specific date"""
        print(f"\n🎯 Generating predictions for: {target_date}")
        
        # Get rainfall data
        print("   Fetching rainfall data...")
        rainfall_data = self.get_rainfall_for_date(target_date)
        print(f"   Rainfall: {rainfall_data['rainfall_24h']:.1f} mm")
        
        # Create prediction grid
        print("   Creating prediction grid...")
        df_grid = self.create_prediction_grid(target_date, rainfall_data)
        print(f"   Grid points: {len(df_grid)}")
        
        # Select features
        feature_columns = self.model_data['feature_names']
        X = df_grid[feature_columns]
        
        # Make predictions
        print("   Running model inference...")
        xgb_model = self.model_data['xgb_model']
        rf_model = self.model_data['rf_model']
        scaler = self.model_data['scaler']
        
        X_scaled = scaler.transform(X)
        
        # Ensemble prediction
        prob_xgb = xgb_model.predict_proba(X_scaled)[:, 1]
        prob_rf = rf_model.predict_proba(X_scaled)[:, 1]
        prob_ensemble = 0.6 * prob_xgb + 0.4 * prob_rf
        
        df_grid['risk_score'] = prob_ensemble
        
        # Filter high-risk points (threshold: 0.6)
        df_high_risk = df_grid[df_grid['risk_score'] > 0.6].copy()
        print(f"   High-risk points: {len(df_high_risk)}")
        
        if len(df_high_risk) == 0:
            print("   ℹ️  No high-risk areas predicted")
            return []
        
        # Cluster high-risk points into hotspots
        print("   Clustering hotspots...")
        hotspots = self.cluster_hotspots(df_high_risk, rainfall_data)
        print(f"   ✅ Generated {len(hotspots)} hotspots")
        
        return hotspots
    
    def cluster_hotspots(self, df_high_risk, rainfall_data):
        """Cluster high-risk points into hotspots using DBSCAN"""
        coords = df_high_risk[['lat', 'lng']].values
        
        # DBSCAN clustering
        # eps in degrees (~0.005 degrees ≈ 500m)
        clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
        df_high_risk['cluster'] = clustering.labels_
        
        # Remove noise points (label = -1)
        df_clustered = df_high_risk[df_high_risk['cluster'] != -1]
        
        hotspots = []
        for cluster_id in df_clustered['cluster'].unique():
            cluster_points = df_clustered[df_clustered['cluster'] == cluster_id]
            
            # Calculate cluster center
            center_lat = cluster_points['lat'].mean()
            center_lng = cluster_points['lng'].mean()
            avg_risk = cluster_points['risk_score'].mean()
            max_risk = cluster_points['risk_score'].max()
            
            # Determine severity
            if max_risk > 0.85:
                severity = 'Critical'
            elif max_risk > 0.75:
                severity = 'High'
            elif max_risk > 0.65:
                severity = 'Medium'
            else:
                severity = 'Low'
            
            # Calculate radius (based on cluster spread)
            distances = np.sqrt(
                (cluster_points['lat'] - center_lat)**2 +
                (cluster_points['lng'] - center_lng)**2
            ) * 111000  # Convert to meters
            radius = max(int(distances.max()), 200)
            
            # Reverse geocode to get name (simplified)
            name = self.get_location_name(center_lat, center_lng)
            
            # Risk factors
            risk_factors = {
                'high_rainfall': rainfall_data['rainfall_24h'] > 50,
                'very_high_rainfall': rainfall_data['rainfall_24h'] > 100,
                'cluster_size': len(cluster_points),
                'max_risk_score': float(max_risk)
            }
            
            hotspots.append({
                'lat': float(center_lat),
                'lng': float(center_lng),
                'name': name,
                'severity': severity,
                'confidence_score': float(avg_risk),
                'predicted_rainfall_mm': rainfall_data['rainfall_24h'],
                'risk_factors': json.dumps(risk_factors),
                'radius_meters': radius
            })
        
        return hotspots
    
    def get_location_name(self, lat, lng):
        """Get location name from coordinates (simplified)"""
        # Known locations
        known_locations = [
            (28.6330, 77.2285, "Minto Bridge Area"),
            (28.6304, 77.2425, "ITO Crossing Area"),
            (28.5910, 77.1610, "Dhaula Kuan Area"),
            (28.6139, 76.9830, "Najafgarh Area"),
            (28.6675, 77.2282, "Kashmere Gate Area"),
        ]
        
        # Find nearest known location
        min_dist = float('inf')
        nearest_name = "Unknown Area"
        
        for known_lat, known_lng, name in known_locations:
            dist = np.sqrt((lat - known_lat)**2 + (lng - known_lng)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_name = name
        
        # If too far from known locations, use generic name
        if min_dist > 0.05:  # ~5km
            return f"Area near {lat:.4f}, {lng:.4f}"
        
        return nearest_name
    
    def save_predictions_to_db(self, target_date, hotspots):
        """Save predictions to database"""
        if not hotspots:
            print("   No hotspots to save")
            return
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # Delete existing predictions for this date
            cur.execute("""
                DELETE FROM predicted_hotspots WHERE prediction_date = %s
            """, (target_date,))
            
            # Insert new predictions
            for hotspot in hotspots:
                cur.execute("""
                    INSERT INTO predicted_hotspots 
                    (prediction_date, name, lat, lng, severity, confidence_score, 
                     predicted_rainfall_mm, risk_factors, radius_meters, model_version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    target_date,
                    hotspot['name'],
                    hotspot['lat'],
                    hotspot['lng'],
                    hotspot['severity'],
                    hotspot['confidence_score'],
                    hotspot['predicted_rainfall_mm'],
                    hotspot['risk_factors'],
                    hotspot['radius_meters'],
                    self.model_data['model_version']
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"   ✅ Saved {len(hotspots)} predictions to database")
        
        except Exception as e:
            print(f"   ❌ Failed to save to database: {e}")

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python predict_for_date.py YYYY-MM-DD")
        sys.exit(1)
    
    target_date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🔮 DATE-BASED WATERLOGGING PREDICTION")
    print("="*70)
    
    predictor = DateBasedPredictor()
    hotspots = predictor.predict_for_date(target_date)
    predictor.save_predictions_to_db(target_date, hotspots)
    
    print("\n" + "="*70)
    print("✨ Prediction completed!")
    print("="*70)

if __name__ == "__main__":
    main()
