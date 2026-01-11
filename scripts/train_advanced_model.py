"""
Advanced ML Model Training for Delhi Waterlogging Prediction
Uses ensemble learning with XGBoost, Random Forest, and temporal features
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import json
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

# Directories
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical')
os.makedirs(MODELS_DIR, exist_ok=True)

class WaterloggingPredictor:
    """Advanced waterlogging prediction model with ensemble learning"""
    
    def __init__(self):
        self.xgb_model = None
        self.rf_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "v2.0.0"
        
    def create_temporal_features(self, df):
        """Create temporal features from date"""
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_year'] = df['date'].dt.dayofyear
        df['month'] = df['date'].dt.month
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Monsoon season flag (June-September)
        df['is_monsoon'] = ((df['month'] >= 6) & (df['month'] <= 9)).astype(int)
        
        # Cyclical encoding for day of year
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        # Cyclical encoding for month
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_spatial_features(self, df):
        """Create spatial features"""
        # Known high-risk zones (based on historical data)
        high_risk_zones = [
            (28.6330, 77.2285),  # Minto Bridge
            (28.6304, 77.2425),  # ITO
            (28.5910, 77.1610),  # Dhaula Kuan
            (28.6139, 76.9830),  # Najafgarh
        ]
        
        # Calculate minimum distance to high-risk zones
        def min_distance_to_risk_zone(row):
            lat, lng = row['lat'], row['lng']
            distances = []
            for risk_lat, risk_lng in high_risk_zones:
                # Haversine distance approximation
                dist = np.sqrt((lat - risk_lat)**2 + (lng - risk_lng)**2) * 111  # km
                distances.append(dist)
            return min(distances)
        
        df['min_dist_to_risk_zone_km'] = df.apply(min_distance_to_risk_zone, axis=1)
        
        # Elevation proxy (lower latitude generally means lower elevation in Delhi)
        df['elevation_proxy'] = 28.7 - df['lat']  # Normalized
        
        return df
    
    def create_rainfall_features(self, df):
        """Create rainfall-based features"""
        # Rainfall intensity categories
        df['rainfall_intensity'] = pd.cut(
            df['rainfall_24h'],
            bins=[0, 15, 35, 65, 115, 1000],
            labels=['Very Light', 'Light', 'Moderate', 'Heavy', 'Very Heavy']
        )
        
        # Convert to numeric
        intensity_map = {'Very Light': 1, 'Light': 2, 'Moderate': 3, 'Heavy': 4, 'Very Heavy': 5}
        df['rainfall_intensity_num'] = df['rainfall_intensity'].map(intensity_map)
        
        # Rainfall squared (non-linear relationship)
        df['rainfall_squared'] = df['rainfall_24h'] ** 2
        
        # Log rainfall (handle zeros)
        df['rainfall_log'] = np.log1p(df['rainfall_24h'])
        
        return df
    
    def prepare_training_data(self):
        """Load and prepare training data"""
        print("\n📊 Preparing training data...")
        
        # Load historical incidents
        incidents_file = os.path.join(DATA_DIR, 'sample_historical_incidents.csv')
        if not os.path.exists(incidents_file):
            raise FileNotFoundError(f"Historical incidents file not found: {incidents_file}")
        
        df_incidents = pd.read_csv(incidents_file)
        print(f"   Loaded {len(df_incidents)} historical incidents")
        
        # Create positive samples (waterlogging occurred)
        positive_samples = df_incidents.copy()
        positive_samples['waterlogging'] = 1
        
        # Create negative samples (no waterlogging)
        # Generate random dates and locations where no waterlogging occurred
        np.random.seed(42)
        n_negative = len(positive_samples) * 3  # 3x negative samples
        
        negative_samples = []
        for _ in range(n_negative):
            # Random date in monsoon season
            year = np.random.randint(2015, 2024)
            month = np.random.randint(6, 10)  # June to September
            day = np.random.randint(1, 29)
            
            # Random location in Delhi
            lat = np.random.uniform(28.4, 28.9)
            lng = np.random.uniform(76.8, 77.4)
            
            # Low rainfall (no waterlogging)
            rainfall = np.random.uniform(0, 30)
            
            negative_samples.append({
                'date': f"{year}-{month:02d}-{day:02d}",
                'location': 'Random',
                'lat': lat,
                'lng': lng,
                'severity': 'Low',
                'depth_cm': 0,
                'duration_h': 0,
                'rainfall_mm': rainfall,
                'waterlogging': 0
            })
        
        df_negative = pd.DataFrame(negative_samples)
        print(f"   Generated {len(df_negative)} negative samples")
        
        # Combine positive and negative samples
        df = pd.concat([positive_samples, df_negative], ignore_index=True)
        
        # Rename columns for consistency
        df = df.rename(columns={'rainfall_mm': 'rainfall_24h'})
        
        # Create features
        df = self.create_temporal_features(df)
        df = self.create_spatial_features(df)
        df = self.create_rainfall_features(df)
        
        # Select features for training
        feature_columns = [
            'rainfall_24h', 'rainfall_squared', 'rainfall_log', 'rainfall_intensity_num',
            'lat', 'lng', 'elevation_proxy', 'min_dist_to_risk_zone_km',
            'day_of_year', 'month', 'is_monsoon',
            'day_sin', 'day_cos', 'month_sin', 'month_cos'
        ]
        
        X = df[feature_columns]
        y = df['waterlogging']
        
        self.feature_names = feature_columns
        
        print(f"   Total samples: {len(df)}")
        print(f"   Positive samples: {sum(y == 1)}")
        print(f"   Negative samples: {sum(y == 0)}")
        print(f"   Features: {len(feature_columns)}")
        
        return X, y, df
    
    def train_models(self, X, y):
        """Train ensemble models"""
        print("\n🤖 Training ensemble models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 1. Train XGBoost
        print("\n   Training XGBoost Classifier...")
        xgb_params = {
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.3],
            'n_estimators': [100, 200],
            'min_child_weight': [1, 3, 5],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0]
        }
        
        xgb_model = xgb.XGBClassifier(
            objective='binary:logistic',
            random_state=42,
            eval_metric='logloss'
        )
        
        # Grid search (limited for speed)
        print("      Running hyperparameter tuning...")
        grid_search = GridSearchCV(
            xgb_model,
            {'max_depth': [5, 7], 'learning_rate': [0.1, 0.3], 'n_estimators': [100, 200]},
            cv=3,
            scoring='f1',
            n_jobs=-1
        )
        grid_search.fit(X_train_scaled, y_train)
        
        self.xgb_model = grid_search.best_estimator_
        print(f"      Best params: {grid_search.best_params_}")
        
        # 2. Train Random Forest
        print("\n   Training Random Forest Classifier...")
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        self.rf_model = rf_model
        
        # Evaluate models
        print("\n📈 Model Evaluation:")
        
        # XGBoost evaluation
        y_pred_xgb = self.xgb_model.predict(X_test_scaled)
        print("\n   XGBoost Performance:")
        print(f"      Precision: {precision_score(y_test, y_pred_xgb):.4f}")
        print(f"      Recall: {recall_score(y_test, y_pred_xgb):.4f}")
        print(f"      F1-Score: {f1_score(y_test, y_pred_xgb):.4f}")
        
        # Random Forest evaluation
        y_pred_rf = self.rf_model.predict(X_test_scaled)
        print("\n   Random Forest Performance:")
        print(f"      Precision: {precision_score(y_test, y_pred_rf):.4f}")
        print(f"      Recall: {recall_score(y_test, y_pred_rf):.4f}")
        print(f"      F1-Score: {f1_score(y_test, y_pred_rf):.4f}")
        
        # Ensemble prediction (weighted voting)
        y_pred_ensemble = (0.6 * y_pred_xgb + 0.4 * y_pred_rf) > 0.5
        print("\n   Ensemble Performance:")
        print(f"      Precision: {precision_score(y_test, y_pred_ensemble):.4f}")
        print(f"      Recall: {recall_score(y_test, y_pred_ensemble):.4f}")
        print(f"      F1-Score: {f1_score(y_test, y_pred_ensemble):.4f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n   Top 5 Important Features:")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"      {row['feature']}: {row['importance']:.4f}")
        
        return {
            'precision': precision_score(y_test, y_pred_ensemble),
            'recall': recall_score(y_test, y_pred_ensemble),
            'f1_score': f1_score(y_test, y_pred_ensemble),
            'feature_importance': feature_importance.to_dict('records')
        }
    
    def predict(self, features_df):
        """Make predictions using ensemble"""
        features_scaled = self.scaler.transform(features_df)
        
        # Get probabilities from both models
        prob_xgb = self.xgb_model.predict_proba(features_scaled)[:, 1]
        prob_rf = self.rf_model.predict_proba(features_scaled)[:, 1]
        
        # Weighted ensemble
        prob_ensemble = 0.6 * prob_xgb + 0.4 * prob_rf
        
        return prob_ensemble
    
    def save_model(self, metrics):
        """Save trained model and metadata"""
        print("\n💾 Saving model...")
        
        # Save model
        model_data = {
            'xgb_model': self.xgb_model,
            'rf_model': self.rf_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_version': self.model_version,
            'metrics': metrics,
            'trained_at': datetime.now().isoformat()
        }
        
        model_file = os.path.join(MODELS_DIR, 'waterlogging_advanced_v2.pkl')
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"   ✅ Model saved to: {model_file}")
        
        # Save metadata as JSON
        metadata = {
            'model_version': self.model_version,
            'trained_at': datetime.now().isoformat(),
            'metrics': {
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'f1_score': float(metrics['f1_score'])
            },
            'feature_names': self.feature_names,
            'feature_importance': metrics['feature_importance'][:10]  # Top 10
        }
        
        metadata_file = os.path.join(MODELS_DIR, 'model_metadata_v2.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"   ✅ Metadata saved to: {metadata_file}")

def main():
    """Main training pipeline"""
    print("\n" + "="*70)
    print("🚀 ADVANCED WATERLOGGING PREDICTION MODEL TRAINING")
    print("="*70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize predictor
    predictor = WaterloggingPredictor()
    
    # Prepare data
    X, y, df = predictor.prepare_training_data()
    
    # Train models
    metrics = predictor.train_models(X, y)
    
    # Save model
    predictor.save_model(metrics)
    
    print("\n" + "="*70)
    print("✨ Training completed successfully!")
    print("="*70)
    print(f"\nModel Performance Summary:")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1-Score: {metrics['f1_score']:.4f}")
    print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    main()
