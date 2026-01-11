# 📋 Historical Predictions - Quick Reference Card

## 🚀 Quick Start (3 Commands)

```bash
# 1. Setup everything
setup_historical_system.bat

# 2. Start server
npm start

# 3. Open browser
http://localhost:3000/predictions.html
```

## 📅 Generate Predictions

### For a specific date:
```bash
python scripts/predict_for_date.py 2024-07-15
```

### For today:
```bash
# Windows PowerShell
python scripts/predict_for_date.py (Get-Date -Format "yyyy-MM-dd")

# Windows CMD
python scripts/predict_for_date.py %date:~-4%-%date:~3,2%-%date:~0,2%
```

### For tomorrow:
```bash
# PowerShell
$tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
python scripts/predict_for_date.py $tomorrow
```

### Batch generate (entire month):
```powershell
# PowerShell - Generate for July 2024
1..31 | ForEach-Object {
    $date = "2024-07-" + $_.ToString("00")
    python scripts/predict_for_date.py $date
}
```

## 🗺️ Using the Web Interface

### Access the Page
1. Navigate to: `http://localhost:3000/predictions.html`
2. Select a date using the date picker
3. Click "Load Predictions"

### Quick Date Selection
- **Today**: Click "Today" button
- **Tomorrow**: Click "Tomorrow" button
- **Next Week**: Click "Next Week" button
- **Yesterday**: Click "Yesterday" button
- **Last Week**: Click "Last Week" button

### Interact with Map
- **Click hotspot**: View detailed popup
- **Zoom**: Scroll wheel or +/- buttons
- **Pan**: Click and drag

### Hotspot List
- **Click hotspot**: Map zooms to location
- **Color coding**:
  - 🔴 Red border = Critical
  - 🟠 Orange border = High
  - 🟡 Yellow border = Medium
  - 🟢 Green border = Low

## 🔧 Maintenance Commands

### Retrain Model
```bash
python scripts/train_advanced_model.py
```

### Update Database Schema
```bash
python scripts/migrate_historical_schema.py
```

### Download New Data
```bash
python scripts/download_comprehensive_data.py
```

### Check Model Performance
```bash
# Access via API
curl http://localhost:3000/api/model/metrics
```

## 📊 API Quick Reference

### Get Predictions for Date
```bash
GET /api/predictions/date/2024-07-15
```

### Get Historical Incidents
```bash
GET /api/historical/incidents?start_date=2024-07-01&end_date=2024-07-31
```

### Get Rainfall Data
```bash
GET /api/rainfall/date/2024-07-15
```

### Get Model Metrics
```bash
GET /api/model/metrics
```

### Generate Prediction (Authority Only)
```bash
POST /api/predictions/generate
Body: { "date": "2024-07-15" }
```

## 🐛 Troubleshooting

### No predictions for selected date
**Solution**: Generate predictions first
```bash
python scripts/predict_for_date.py 2024-07-15
```

### Model not found error
**Solution**: Train the model
```bash
python scripts/train_advanced_model.py
```

### Database connection error
**Solution**: Check `.env` file has correct `DATABASE_URL`

### Import errors
**Solution**: Install dependencies
```bash
pip install -r ml_requirements.txt
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `predictions.html` | Main UI page |
| `predictions.js` | Frontend logic |
| `server/index.js` | Backend API |
| `scripts/predict_for_date.py` | Prediction generator |
| `scripts/train_advanced_model.py` | Model trainer |
| `models/waterlogging_advanced_v2.pkl` | Trained model |

## 🎯 Severity Levels

| Level | Color | Description |
|-------|-------|-------------|
| **Critical** | 🔴 Red | Severe waterlogging expected (>100mm rain) |
| **High** | 🟠 Orange | Significant waterlogging likely (65-100mm) |
| **Medium** | 🟡 Yellow | Moderate waterlogging possible (35-65mm) |
| **Low** | 🟢 Green | Minor waterlogging may occur (15-35mm) |

## 📈 Model Features (Top 5)

1. **rainfall_24h** - 24-hour rainfall amount
2. **min_dist_to_risk_zone_km** - Distance to known hotspots
3. **is_monsoon** - Monsoon season flag
4. **elevation_proxy** - Topography indicator
5. **rainfall_squared** - Non-linear rainfall effect

## 🔐 User Roles

### Citizens
- ✅ View predictions
- ✅ Select dates
- ✅ View statistics
- ❌ Cannot trigger predictions

### Authorities
- ✅ View predictions
- ✅ Select dates
- ✅ View statistics
- ✅ Trigger prediction generation
- ✅ Access model metrics

## 💡 Pro Tips

1. **Pre-generate predictions** for monsoon season (June-Sept)
2. **Retrain model monthly** with new incident data
3. **Compare predictions** with actual incidents for validation
4. **Use quick date buttons** for faster navigation
5. **Check confidence scores** - Higher = more reliable

## 📞 Need Help?

1. Check `HISTORICAL_PREDICTION_SETUP.md` for detailed setup
2. Review `IMPLEMENTATION_SUMMARY.md` for system overview
3. See `HISTORICAL_PREDICTION_PLAN.md` for architecture
4. Check console logs for error messages

## ⚡ Performance Tips

### Speed up predictions:
```python
# In predict_for_date.py, increase grid size
grid_size = 0.02  # Larger = faster but less accurate
```

### Cache predictions:
```bash
# Pre-generate for common dates
python scripts/predict_for_date.py 2024-07-15
python scripts/predict_for_date.py 2024-08-15
python scripts/predict_for_date.py 2024-09-15
```

### Optimize database:
```sql
-- Run in PostgreSQL
VACUUM ANALYZE predicted_hotspots;
REINDEX TABLE predicted_hotspots;
```

## 🎉 Success Checklist

- [ ] Database tables created
- [ ] Historical data downloaded
- [ ] Model trained successfully
- [ ] Predictions generated for test date
- [ ] Web interface accessible
- [ ] Map displays hotspots
- [ ] Statistics showing correctly
- [ ] API endpoints responding

---

**Quick Reference Version**: 1.0
**Last Updated**: 2026-01-11
**For**: Delhi Waterlogging Prediction System v2.0
