# 🚀 SETUP INSTRUCTIONS - Historical Prediction System

## ⚡ Quick Start (Follow These Steps)

### Step 1: Install Python Dependencies ✅ (Running now...)
```bash
pip install -r ml_requirements.txt
```
**Status**: Installing packages (pandas, numpy, scikit-learn, xgboost, etc.)
**Time**: ~2-5 minutes

---

### Step 2: Setup Database Tables
```bash
python scripts/migrate_historical_schema.py
```
**What it does**: Creates 4 new tables in your database:
- `historical_incidents` - Past waterlogging events
- `historical_rainfall` - Rainfall data
- `predicted_hotspots` - Date-based predictions
- `model_metadata` - Model performance tracking

**Time**: ~10 seconds

---

### Step 3: Download Historical Data
```bash
python scripts/download_comprehensive_data.py
```
**What it does**: 
- Downloads sample historical incidents (15 real events)
- Creates Delhi waterlogging spots database (20 locations)
- Generates sample rainfall data
- Creates instructions for manual downloads

**Time**: ~30 seconds

---

### Step 4: Train the ML Model
```bash
python scripts/train_advanced_model.py
```
**What it does**:
- Generates 50,000+ training samples
- Trains XGBoost + Random Forest ensemble
- Performs hyperparameter tuning
- Saves model to `models/waterlogging_advanced_v2.pkl`

**Time**: ~10-30 minutes (depending on your computer)
**Note**: This is the longest step - be patient!

---

### Step 5: Generate Your First Prediction
```bash
python scripts/predict_for_date.py 2024-07-15
```
**What it does**:
- Fetches rainfall data for the date
- Runs model inference on Delhi grid
- Clusters hotspots using DBSCAN
- Saves predictions to database

**Time**: ~30-60 seconds

---

### Step 6: Start the Server
```bash
npm start
```
**What it does**: Starts the Node.js backend server

**Time**: ~2 seconds

---

### Step 7: Open the Predictions Page
Open your browser and go to:
```
http://localhost:3000/predictions.html
```

---

## 🎯 What You'll See

1. **Date Picker** - Select any date
2. **Interactive Map** - See predicted hotspots
3. **Statistics** - Total hotspots, severity breakdown
4. **Hotspot List** - Detailed list with confidence scores
5. **Model Info** - Performance metrics

---

## ⚠️ Important Notes

### Database Connection
Make sure you have a `.env` file with:
```
DATABASE_URL=your_supabase_connection_string
```

### If Step 4 (Training) Takes Too Long
You can reduce the training data size by editing `scripts/train_advanced_model.py`:
```python
# Line ~95: Reduce negative samples
n_negative = len(positive_samples) * 1  # Change from 3 to 1
```

### If You Get Errors
1. **Import Error**: Run `pip install -r ml_requirements.txt` again
2. **Database Error**: Check your `.env` file has correct `DATABASE_URL`
3. **Model Not Found**: Make sure Step 4 (training) completed successfully

---

## 📊 Expected Results

After setup, you should have:
- ✅ 4 new database tables
- ✅ Trained model file (~50MB)
- ✅ Sample historical data
- ✅ Predictions for at least one date
- ✅ Working web interface

---

## 🎉 Success Checklist

- [ ] Step 1: Python packages installed
- [ ] Step 2: Database tables created
- [ ] Step 3: Historical data downloaded
- [ ] Step 4: Model trained (this takes longest!)
- [ ] Step 5: First prediction generated
- [ ] Step 6: Server started
- [ ] Step 7: Web page opens and shows predictions

---

## 💡 Pro Tips

1. **Run steps in order** - Don't skip any step
2. **Step 4 is the longest** - Go get coffee while it trains
3. **Check for errors** - Read the console output
4. **Test with a date** - Try 2024-07-15 (monsoon season)

---

## 🆘 Need Help?

If you get stuck:
1. Check the error message in console
2. Look at `QUICK_REFERENCE.md` for troubleshooting
3. Make sure all previous steps completed successfully

---

**Ready to start? Follow the steps above one by one!**
