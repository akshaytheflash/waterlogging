# Historical Waterlogging Prediction System - Implementation Plan

## Overview
This document outlines the implementation of a **Historical Prediction System** that allows users to select any date and view predicted waterlogging hotspots for that specific date based on a well-trained ML model using extensive Delhi waterlogging and rainfall data.

## Current System vs New System

### Current System (24h Prediction)
- Real-time prediction for next 24 hours
- Uses current weather data
- Limited historical context
- Basic DBSCAN clustering

### New System (Date-Based Historical Prediction)
- **Date Selection**: Users can select any date (past or future)
- **Historical Analysis**: View what happened on similar dates in the past
- **Comprehensive Training Data**: Model trained on 10+ years of data
- **Advanced Features**: Seasonal patterns, monsoon intensity, multi-year trends

## Data Sources

### 1. IIT Delhi HydroSense Lab
- **INDOFLOODS Dataset**: Comprehensive flood events database
- **India Flood Inventory**: Geospatial dataset of floods over India
- **URL**: https://hydrosense.iitd.ac.in/resources/
- **Format**: Zenodo datasets (CSV, GeoJSON)

### 2. Waterhubdata.com (IIT Delhi)
- **Barapullah Sub-basin Waterlogging Data (2021)**
- **Temporal Coverage**: July 15 - September 30, 2021
- **Format**: CSV, GeoJSON, Shapefile
- **URL**: waterhubdata.com dataset ID: 20210917_I13_WL_BARAPULLAH_MP002

### 3. IMD (India Meteorological Department)
- **Delhi Rainfall Data (1901-2021)**
- **Granularity**: Monthly and Daily
- **Source**: Open Government Data Platform India
- **Format**: CSV

### 4. OpenCity.in
- **Delhi Rainfall Historical Data**
- **Coverage**: North and South Delhi
- **Format**: CSV

### 5. Additional Sources
- **Delhi Traffic Police Reports**: 308 critical waterlogging spots (2023)
- **DDMA (Delhi Disaster Management Authority)**: Flood reports
- **News Archives**: Historical waterlogging incidents

## Database Schema Updates

### New Tables

```sql
-- Historical Waterlogging Incidents (Ground Truth)
CREATE TABLE IF NOT EXISTS historical_incidents (
    id SERIAL PRIMARY KEY,
    incident_date DATE NOT NULL,
    location_name VARCHAR(200),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    water_depth_cm INTEGER,
    duration_hours INTEGER,
    affected_area_sqm INTEGER,
    source VARCHAR(100), -- 'IIT_Delhi', 'Traffic_Police', 'News', 'User_Report'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical Rainfall Data
CREATE TABLE IF NOT EXISTS historical_rainfall (
    id SERIAL PRIMARY KEY,
    record_date DATE NOT NULL,
    station_name VARCHAR(100),
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    rainfall_mm DECIMAL(6, 2) NOT NULL,
    rainfall_1h DECIMAL(6, 2),
    rainfall_3h DECIMAL(6, 2),
    rainfall_6h DECIMAL(6, 2),
    rainfall_24h DECIMAL(6, 2),
    temperature_c DECIMAL(4, 2),
    humidity_percent INTEGER,
    source VARCHAR(100), -- 'IMD', 'Open-Meteo', 'Manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_date, station_name)
);

-- Predicted Hotspots (Date-based)
CREATE TABLE IF NOT EXISTS predicted_hotspots (
    id SERIAL PRIMARY KEY,
    prediction_date DATE NOT NULL,
    name VARCHAR(200),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    confidence_score DECIMAL(4, 3), -- 0.000 to 1.000
    predicted_rainfall_mm DECIMAL(6, 2),
    risk_factors TEXT, -- JSON string with contributing factors
    radius_meters INTEGER DEFAULT 200,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prediction_date, lat, lng)
);

-- Model Training Metadata
CREATE TABLE IF NOT EXISTS model_metadata (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) UNIQUE NOT NULL,
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_samples INTEGER,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    feature_importance TEXT, -- JSON
    hyperparameters TEXT, -- JSON
    data_sources TEXT, -- JSON array
    notes TEXT
);
```

### Update Existing Hotspots Table

```sql
-- Add columns to existing hotspots table
ALTER TABLE hotspots ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';
ALTER TABLE hotspots ADD COLUMN IF NOT EXISTS prediction_date DATE;
ALTER TABLE hotspots ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(4, 3);
ALTER TABLE hotspots ADD COLUMN IF NOT EXISTS radius_meters INTEGER DEFAULT 200;
ALTER TABLE hotspots ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

## Machine Learning Architecture

### Model Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  • Historical Incidents (IIT Delhi, Traffic Police)         │
│  • Rainfall Data (IMD 1901-2021, 120 years)                 │
│  • Topography (NASA SRTM)                                    │
│  • Infrastructure (OpenStreetMap)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  FEATURE ENGINEERING LAYER                   │
├─────────────────────────────────────────────────────────────┤
│  Temporal Features:                                          │
│    • Day of year, Month, Monsoon season flag                │
│    • Cumulative rainfall (1h, 3h, 6h, 24h, 7d)              │
│    • Soil saturation proxy (3-day weighted rainfall)        │
│    • Days since last heavy rain                              │
│                                                              │
│  Spatial Features:                                           │
│    • Elevation, Slope, Aspect                                │
│    • Distance to nearest drain/river                         │
│    • Road density, Impervious surface ratio                  │
│    • Historical incident density (500m radius)               │
│                                                              │
│  Weather Features:                                           │
│    • Rainfall intensity (mm/h)                               │
│    • Temperature, Humidity                                   │
│    • Similar historical day patterns                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      MODEL ENSEMBLE                          │
├─────────────────────────────────────────────────────────────┤
│  Model 1: XGBoost Classifier                                 │
│    • Binary classification (Waterlogging: Yes/No)           │
│    • Grid cell level (100m × 100m)                          │
│    • Output: Risk probability (0-1)                         │
│                                                              │
│  Model 2: Random Forest Regressor                            │
│    • Severity prediction (Low/Medium/High/Critical)         │
│    • Water depth estimation                                  │
│    • Duration prediction                                     │
│                                                              │
│  Model 3: LSTM (Time Series)                                 │
│    • Captures temporal dependencies                         │
│    • Monsoon pattern learning                               │
│    • Multi-day rainfall sequences                           │
│                                                              │
│  Ensemble Strategy: Weighted Voting                          │
│    • XGBoost: 50% weight (primary)                          │
│    • Random Forest: 30% weight                              │
│    • LSTM: 20% weight                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   CLUSTERING & HOTSPOT GEN                   │
├─────────────────────────────────────────────────────────────┤
│  • HDBSCAN (Hierarchical DBSCAN)                            │
│  • Adaptive eps based on urban density                       │
│  • Min cluster size: 3 cells                                 │
│  • Noise filtering                                           │
│  • Reverse geocoding for names                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT & PERSISTENCE                      │
├─────────────────────────────────────────────────────────────┤
│  • Store in predicted_hotspots table                        │
│  • Generate confidence scores                                │
│  • Create risk factor explanations                          │
│  • Cache predictions for performance                         │
└─────────────────────────────────────────────────────────────┘
```

### Training Strategy

**Dataset Size Target**: 50,000+ labeled samples
- Historical incidents: ~5,000 records (2010-2024)
- Synthetic augmentation: ~45,000 records
  - Based on topography + extreme rainfall events
  - Validated against known patterns

**Training Splits**:
- Training: 70% (2010-2020)
- Validation: 15% (2021-2022)
- Test: 15% (2023-2024)

**Cross-Validation**:
- 5-Fold Temporal Cross-Validation
- Ensures no data leakage from future to past

**Hyperparameter Tuning**:
- Grid Search with 100+ combinations
- Bayesian Optimization for final tuning
- Target: F1-Score > 0.75

## Python Scripts to Implement

### 1. `scripts/download_historical_data.py`
Downloads all historical data from sources

### 2. `scripts/process_iit_delhi_data.py`
Processes IIT Delhi waterlogging datasets

### 3. `scripts/import_imd_rainfall.py`
Imports IMD rainfall data (1901-2021)

### 4. `scripts/generate_training_dataset.py`
Creates the final training dataset with all features

### 5. `scripts/train_advanced_model.py`
Trains the ensemble model

### 6. `scripts/predict_for_date.py`
Generates predictions for a specific date

### 7. `scripts/batch_predict_historical.py`
Pre-computes predictions for common date ranges

## Backend API Endpoints

### New Endpoints

```javascript
// Get predicted hotspots for a specific date
GET /api/predictions/date/:date
Response: {
  date: "2024-07-15",
  hotspots: [
    {
      id: 1,
      name: "Minto Bridge Area",
      lat: 28.6330,
      lng: 77.2285,
      severity: "Critical",
      confidence: 0.892,
      predicted_rainfall: 85.5,
      risk_factors: {
        "high_rainfall": true,
        "low_elevation": true,
        "poor_drainage": true,
        "historical_incidents": 12
      },
      radius_meters: 350
    }
  ],
  model_version: "v2.1.0",
  total_count: 15
}

// Get historical incidents for a date range
GET /api/historical/incidents?start_date=2023-07-01&end_date=2023-07-31
Response: {
  incidents: [...],
  total_count: 45
}

// Get model performance metrics
GET /api/model/metrics
Response: {
  current_version: "v2.1.0",
  accuracy: 0.8234,
  precision: 0.7891,
  recall: 0.7654,
  f1_score: 0.7771,
  training_samples: 52341,
  last_trained: "2024-01-10T10:30:00Z"
}

// Get rainfall data for a date
GET /api/rainfall/date/:date
Response: {
  date: "2024-07-15",
  stations: [
    {
      name: "Safdarjung",
      rainfall_24h: 85.5,
      temperature: 32.5,
      humidity: 78
    }
  ]
}
```

## Frontend Implementation

### New Page: `public/predictions.html`

**Features**:
1. **Date Picker**: Calendar interface to select any date
2. **Interactive Map**: Shows predicted hotspots for selected date
3. **Confidence Indicators**: Visual representation of prediction confidence
4. **Historical Context**: Shows similar past incidents
5. **Risk Factors**: Explains why each hotspot is predicted
6. **Comparison View**: Compare predictions vs actual incidents (for past dates)
7. **Download Options**: Export predictions as CSV/JSON

**UI Components**:
- Date range selector (single date or range)
- Map with color-coded hotspots (confidence-based)
- Sidebar with hotspot details
- Charts showing rainfall patterns
- Model performance dashboard

### Navigation Update

Add new menu item to `navbar.js`:
```javascript
{
  name: 'Historical Predictions',
  href: '/predictions.html',
  icon: '📊'
}
```

## Data Collection Workflow

### Phase 1: Automated Downloads (Week 1)
1. Download IIT Delhi datasets from Zenodo
2. Download IMD rainfall data from OGD Platform
3. Download Waterhubdata.com Barapullah dataset
4. Scrape Delhi Traffic Police waterlogging spot data

### Phase 2: Data Cleaning (Week 1-2)
1. Standardize date formats
2. Geocode location names to lat/lng
3. Remove duplicates
4. Validate coordinates (within Delhi bounds)
5. Merge overlapping incidents

### Phase 3: Feature Engineering (Week 2)
1. Calculate elevation for each incident
2. Compute distance to drains
3. Generate temporal features
4. Create grid-based aggregations

### Phase 4: Model Training (Week 2-3)
1. Train XGBoost classifier
2. Train Random Forest regressor
3. Train LSTM for temporal patterns
4. Ensemble combination
5. Hyperparameter tuning

### Phase 5: Validation (Week 3)
1. Test on 2023-2024 data
2. Compare with actual incidents
3. Calculate performance metrics
4. Adjust thresholds

### Phase 6: Deployment (Week 4)
1. Integrate with backend
2. Create prediction cache
3. Deploy frontend
4. User testing

## Performance Optimization

### Caching Strategy
- Pre-compute predictions for monsoon season (June-September)
- Cache predictions for 1 year
- Invalidate cache when model is retrained

### Database Indexing
```sql
CREATE INDEX idx_historical_incidents_date ON historical_incidents(incident_date);
CREATE INDEX idx_historical_rainfall_date ON historical_rainfall(record_date);
CREATE INDEX idx_predicted_hotspots_date ON predicted_hotspots(prediction_date);
CREATE INDEX idx_predicted_hotspots_location ON predicted_hotspots(lat, lng);
```

### API Response Time Targets
- Date prediction lookup: < 200ms (cached)
- Fresh prediction generation: < 5s
- Historical incidents query: < 300ms

## Success Metrics

### Model Performance
- **Precision**: > 75% (minimize false alarms)
- **Recall**: > 70% (catch most incidents)
- **F1-Score**: > 0.75
- **Spatial Accuracy**: < 500m average error

### User Experience
- Page load time: < 2s
- Prediction generation: < 5s
- Map rendering: < 1s
- Mobile responsive: Yes

### Data Quality
- Training samples: > 50,000
- Historical coverage: 10+ years
- Spatial coverage: All Delhi districts
- Data sources: 5+ verified sources

## Risk Mitigation

### Data Quality Risks
- **Risk**: Incomplete historical data
- **Mitigation**: Use synthetic data generation + validation

### Model Performance Risks
- **Risk**: Overfitting to historical patterns
- **Mitigation**: Temporal cross-validation + regularization

### API Performance Risks
- **Risk**: Slow prediction generation
- **Mitigation**: Pre-computation + caching + async processing

## Timeline

**Week 1**: Data collection and cleaning
**Week 2**: Feature engineering and initial training
**Week 3**: Model optimization and validation
**Week 4**: Backend integration and frontend development
**Week 5**: Testing and deployment

## Next Steps

1. ✅ Review and approve this plan
2. ⏳ Set up data download scripts
3. ⏳ Create database migrations
4. ⏳ Implement data processing pipeline
5. ⏳ Train initial model
6. ⏳ Build prediction API
7. ⏳ Create frontend interface
8. ⏳ Deploy and test

---

**Document Version**: 1.0
**Last Updated**: 2026-01-11
**Author**: Antigravity AI Assistant
