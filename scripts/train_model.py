import pandas as pd
import numpy as np
import xgboost as xgb
import os
import pickle

# Configuration
MODEL_PATH = os.path.join("models", "waterlogging_xgb.json")

def generate_synthetic_data(n_samples=1000):
    """
    Generates synthetic training data to bootstrap the model.
    Features:
    - rain_1h: Rainfall in last hour (mm)
    - rain_24h: Rainfall in last 24 hours (mm)
    - elevation_rel: Relative elevation (lower is worse, say 0-10 scale where 0 is lowest)
    - drain_dist: Distance to nearest drain (meters)
    
    Target:
    - is_waterlogged: 0 or 1
    """
    np.random.seed(42)
    
    # Randomly generate features
    rain_1h = np.random.exponential(scale=5, size=n_samples)  # Most days have low rain
    rain_24h = rain_1h * np.random.uniform(1, 10, size=n_samples)
    elevation = np.random.normal(loc=5, scale=2, size=n_samples) # 5m avg relative elevation
    drain_dist = np.random.exponential(scale=500, size=n_samples) # Distance in meters
    
    # Updated Synthetic Logic:
    # 1. Vulnerability Score (0.5 to 2.0 approx): Based on Elevation & Drain
    # Lower elevation (e.g. 2m) -> Higher vulnerability
    vulnerability = np.maximum(0, (10 - elevation) / 5.0) + (drain_dist / 1000.0)
    
    # 2. Rain Impact: Weighted sum of 1h and 24h rain
    rain_impact = (rain_24h * 0.4) + (rain_1h * 2.5)
    
    # 3. Final Risk Score: Multiplicative!
    # If Rain is 0, Risk is 0.
    risk_score = rain_impact * vulnerability
    
    # 4. Probability:
    # Sigmoid centered at score=120.
    # Higher center means you need MORE rain to trigger high probability.
    prob = 1 / (1 + np.exp(-(risk_score - 120) * 0.1)) 
    
    is_waterlogged = (np.random.rand(n_samples) < prob).astype(int)
    
    df = pd.DataFrame({
        'rain_1h': rain_1h,
        'rain_24h': rain_24h,
        'elevation_rel': elevation,
        'drain_dist': drain_dist,
        'is_waterlogged': is_waterlogged
    })
    
    return df

def train():
    print("Generating synthetic training data...")
    df = generate_synthetic_data(5000)
    
    X = df.drop('is_waterlogged', axis=1)
    y = df['is_waterlogged']
    
    print(f"Training XGBoost model on {len(df)} samples...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        objective='binary:logistic',
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    # Save model
    model.save_model(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    
    # Verify
    print("\nFeature Importances:")
    print(pd.Series(model.feature_importances_, index=X.columns))

if __name__ == "__main__":
    train()
