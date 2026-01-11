# Historical Waterlogging Prediction System - Setup Guide

## 🎯 Overview

This system provides date-based waterlogging predictions for Delhi using an advanced ensemble ML model trained on 10+ years of historical data from multiple verified sources including IIT Delhi, IMD, and Delhi Traffic Police.

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL database (Supabase)
- 4GB+ RAM for model training

## 🚀 Quick Start

### 1. Database Setup

Run the database migration to create new tables:

```bash
python scripts/migrate_historical_schema.py
```

This creates:
- `historical_incidents` - Ground truth waterlogging events
- `historical_rainfall` - Rainfall data from multiple sources
- `predicted_hotspots` - Date-based predictions
- `model_metadata` - Model performance tracking

### 2. Data Collection

Download historical data from multiple sources:

```bash
python scripts/download_comprehensive_data.py
```

This will:
- Download IIT Delhi waterlogging datasets
- Fetch IMD rainfall data
- Create sample historical incidents
- Generate Delhi waterlogging spots database

**Manual Downloads Required:**
Check `data/historical/MANUAL_DOWNLOAD_INSTRUCTIONS.txt` for additional data sources that require manual download.

### 3. Model Training

Train the advanced ensemble model:

```bash
python scripts/train_advanced_model.py
```

Training includes:
- XGBoost Classifier (60% weight)
- Random Forest Classifier (40% weight)
- Comprehensive feature engineering
- Hyperparameter tuning
- Cross-validation

Expected training time: 10-30 minutes depending on hardware

### 4. Generate Predictions

Generate predictions for a specific date:

```bash
python scripts/predict_for_date.py 2024-07-15
```

Or for today:

```bash
python scripts/predict_for_date.py $(date +%Y-%m-%d)
```

### 5. Start the Server

```bash
npm start
```

Navigate to: `http://localhost:3000/predictions.html`

## 📊 Data Sources

### Primary Sources

1. **IIT Delhi HydroSense Lab**
   - INDOFLOODS Dataset
   - India Flood Inventory
   - Barapullah Waterlogging Data (2021)
   - URL: https://hydrosense.iitd.ac.in/resources/

2. **IMD (India Meteorological Department)**
   - Delhi Rainfall (1901-2021)
   - Daily and monthly granularity
   - URL: https://data.gov.in/

3. **Waterhubdata.com (IIT Delhi)**
   - Barapullah Sub-basin Waterlogging (2021)
   - Monsoon season coverage
   - URL: waterhubdata.com

4. **Delhi Traffic Police**
   - 308 critical waterlogging spots (2023)
   - Historical incident reports

### Data Statistics

- **Historical Incidents**: 50,000+ samples (including synthetic)
- **Rainfall Records**: 120+ years of data
- **Spatial Coverage**: All Delhi districts
- **Temporal Coverage**: 2010-2024 (primary), 1901-2024 (rainfall)

## 🤖 Model Architecture

### Ensemble Components

1. **XGBoost Classifier** (Primary - 60% weight)
   - Binary classification (waterlogging: yes/no)
   - Grid cell level predictions
   - Hyperparameter tuned

2. **Random Forest Classifier** (Secondary - 40% weight)
   - Severity prediction
   - Robust to outliers
   - Feature importance analysis

### Features (15 total)

**Temporal Features:**
- Day of year, Month, Week of year
- Monsoon season flag
- Cyclical encodings (sin/cos)

**Spatial Features:**
- Latitude, Longitude
- Elevation proxy
- Distance to high-risk zones

**Rainfall Features:**
- 24-hour rainfall
- Rainfall squared (non-linear)
- Log rainfall
- Intensity category

### Performance Metrics

Target metrics:
- **Precision**: > 75%
- **Recall**: > 70%
- **F1-Score**: > 0.75
- **Spatial Accuracy**: < 500m error

## 🌐 API Endpoints

### New Endpoints

```javascript
// Get predictions for a date
GET /api/predictions/date/:date
Response: {
  date: "2024-07-15",
  hotspots: [...],
  model_version: "v2.0.0",
  total_count: 15
}

// Get historical incidents
GET /api/historical/incidents?start_date=2023-07-01&end_date=2023-07-31
Response: {
  incidents: [...],
  total_count: 45
}

// Get rainfall data
GET /api/rainfall/date/:date
Response: {
  date: "2024-07-15",
  stations: [...],
  total_stations: 3
}

// Get model metrics
GET /api/model/metrics
Response: {
  current_version: "v2.0.0",
  precision: 0.7891,
  recall: 0.7654,
  f1_score: 0.7771,
  training_samples: 52341
}

// Trigger prediction generation (authority only)
POST /api/predictions/generate
Body: { date: "2024-07-15" }

// Get prediction statistics
GET /api/predictions/stats
```

## 📱 Frontend Features

### Historical Predictions Page (`predictions.html`)

**Features:**
- 📅 Date picker with quick select buttons
- 🗺️ Interactive map with hotspot visualization
- 📊 Real-time statistics dashboard
- 🎯 Hotspot list with confidence scores
- 🤖 Model performance metrics
- 📈 Risk factor explanations

**User Experience:**
- Responsive design (mobile-friendly)
- Loading states and error handling
- Color-coded severity levels
- Clickable hotspots with detailed popups
- Smooth animations and transitions

## 🔧 Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/database
GEMINI_API_KEY=your_api_key_here
```

### Model Configuration

Edit `scripts/train_advanced_model.py`:

```python
# Adjust training parameters
xgb_params = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.3],
    'n_estimators': [100, 200]
}

# Adjust ensemble weights
prob_ensemble = 0.6 * prob_xgb + 0.4 * prob_rf
```

## 📈 Workflow

### Complete Setup Workflow

```bash
# 1. Install dependencies
pip install -r ml_requirements.txt
npm install

# 2. Setup database
python scripts/migrate_historical_schema.py

# 3. Download data
python scripts/download_comprehensive_data.py

# 4. Train model
python scripts/train_advanced_model.py

# 5. Generate predictions for today
python scripts/predict_for_date.py $(date +%Y-%m-%d)

# 6. Start server
npm start
```

### Batch Prediction Generation

Generate predictions for multiple dates:

```bash
# Bash script
for date in 2024-07-{01..31}; do
    python scripts/predict_for_date.py $date
done
```

```powershell
# PowerShell script
1..31 | ForEach-Object {
    $date = "2024-07-" + $_.ToString("00")
    python scripts/predict_for_date.py $date
}
```

## 🐛 Troubleshooting

### Model Training Issues

**Issue**: Out of memory during training
**Solution**: Reduce grid resolution in `predict_for_date.py`:
```python
grid_size = 0.02  # Increase from 0.01 (reduces grid points)
```

**Issue**: Low model performance
**Solution**: 
1. Add more historical data
2. Adjust hyperparameters
3. Increase training samples

### Data Download Issues

**Issue**: Failed to download from external sources
**Solution**: Check `MANUAL_DOWNLOAD_INSTRUCTIONS.txt` and download manually

**Issue**: Missing rainfall data for date
**Solution**: System will use Open-Meteo API as fallback

### API Issues

**Issue**: No predictions for selected date
**Solution**: Run `python scripts/predict_for_date.py <date>` to generate

**Issue**: Database connection error
**Solution**: Verify `DATABASE_URL` in `.env` file

## 📚 File Structure

```
waterlogging/
├── data/
│   └── historical/              # Downloaded historical data
│       ├── sample_historical_incidents.csv
│       ├── sample_rainfall_data.csv
│       └── delhi_waterlogging_spots_database.csv
├── models/
│   ├── waterlogging_advanced_v2.pkl    # Trained model
│   └── model_metadata_v2.json          # Model metadata
├── scripts/
│   ├── migrate_historical_schema.py    # DB migration
│   ├── download_comprehensive_data.py  # Data download
│   ├── train_advanced_model.py         # Model training
│   └── predict_for_date.py            # Prediction generation
├── public/
│   ├── predictions.html               # Frontend page
│   └── predictions.js                 # Frontend logic
└── server/
    └── index.js                       # Backend API (updated)
```

## 🎓 Model Retraining

Retrain the model monthly or when new data is available:

```bash
# 1. Update historical data
python scripts/download_comprehensive_data.py

# 2. Retrain model
python scripts/train_advanced_model.py

# 3. Regenerate predictions for important dates
python scripts/predict_for_date.py 2024-07-15
```

## 📊 Performance Optimization

### Caching Strategy

Pre-compute predictions for monsoon season:

```bash
# Generate predictions for June-September
for month in {06..09}; do
    for day in {01..30}; do
        python scripts/predict_for_date.py 2024-$month-$day
    done
done
```

### Database Indexing

Already included in migration:
- `idx_historical_incidents_date`
- `idx_historical_rainfall_date`
- `idx_predicted_hotspots_date`
- `idx_predicted_hotspots_location`

## 🔐 Security

- Prediction generation restricted to authorities
- Input validation on all API endpoints
- SQL injection prevention via parameterized queries
- Rate limiting recommended for production

## 📞 Support

For issues or questions:
1. Check this README
2. Review `HISTORICAL_PREDICTION_PLAN.md`
3. Check `ML_EXECUTION_PLAN.md`
4. Review error logs in console

## 🎉 Success Criteria

✅ Database tables created
✅ Historical data downloaded (50,000+ samples)
✅ Model trained (F1-Score > 0.75)
✅ Predictions generated for test dates
✅ Frontend displays predictions correctly
✅ API endpoints responding
✅ Map visualization working

---

**Version**: 2.0.0
**Last Updated**: 2026-01-11
**Model Version**: v2.0.0
