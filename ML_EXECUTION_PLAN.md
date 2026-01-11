# ML Execution Plan: Waterlogging Detection & Hotspot Visualization

## 1. Problem Definition
The goal is to transition from static/fake data to a dynamic, predictive system that identifies **waterlogging hotspots** and **predicts flood risk** in real-time.

**What the ML system predicts:**
1.  **Waterlogging Probability Score (0-100%):** The likelihood of a specific geolocation ($lat, lng$) experiencing waterlogging given current/forecasted rainfall.
2.  **Dynamic Hotspot Clusters:** Groups of high-risk coordinates that form a "hotspot" entity (e.g., "Minto Bridge Area").
3.  **Severity Classification:** Auto-classification of user reports (Low/Medium/High/Critical) based on image analysis and text description (Natural Language Processing & Computer Vision).

---

## 2. Data Sources

| Data Type | Source | Type | Format | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Rainfall (Historical & Forecast)** | [Open-Meteo API](https://open-meteo.com/) or IMD (Indian Meteorological Dept) | Public/Free | JSON API | Provides hourly rainfall (mm) & forecasts. |
| **Elevation/Topography** | NASA SRTM (Shuttle Radar Topography Mission) | Public | GeoTIFF / Raster | Critical for flow modeling. Water flows to local minima. |
| **Urban Infrastructure (Roads/Drains)** | OpenStreetMap (OSM) via `osmnx` | Public | GeoJSON / Vector | Road density, surface type (impervious vs porous). |
| **Crowdsourced Incidents** | Internal Postgres DB (`reports` table) | Private | SQL / CSV | Ground truth labels. Lat/Lng + Severity + Timeline. |
| **Satellite Imagery (Optional)** | Sentinel-2 (via Sentinel Hub) | Public | Raster | Post-event flood mapping (swath analysis), useful for validation. |

---

## 3. Data Ingestion Pipeline

**Strategy:** A hybrid approach using **Batch Processing** for training and **On-Demand/Scheduled** fetching for inference.

1.  **Static Data (Ingest Once/Monthly):**
    *   **Elevation & Infrastructure:** Download GeoTIFFs and OSM dumps for the Delhi NCR region.
    *   **Storage:** PostGIS (extension for PostgreSQL) or object storage (AWS S3 / efficient local directory structure for rasters).

2.  **Dynamic Data (Ingest Hourly):**
    *   **Rainfall:** Python script creating a cron job to query Open-Meteo API every hour for Delhi's coordinates.
    *   **User Reports:** Extract recent reports from Supabase `reports` table.
    *   **Storage:** Append to a `feature_store` table in Postgres or a time-series DB (like TimescaleDB).

---

## 4. Data Preprocessing & Feature Engineering

**4.1 Geospatial Preprocessing:**
*   **Gridding:** Divide Delhi into a hexagonal H3 grid (or 100m x 100m square grid). Each cell becomes a data point.
*   **Elevation Features:** Calculate `slope`, `aspect`, and `relative_elevation` (Z-score relative to neighbors) for each grid cell.
*   **Distance Features:** Distance to nearest major drain (from OSM).

**4.2 Temporal Features:**
*   **Cumulative Rainfall:** Sum of rainfall in the last 1h, 3h, 6h, 12h, 24h.
*   **Soil Saturation Proxy:** Rainfall in previous 3 days (decaying sum).

**4.3 Dataset Construction:**
*   **X (Features):** `[rain_1h, rain_24h, relative_elevation, distance_to_drain, impervious_surface_ratio, month]`
*   **y (Target):** Binary (1 if >N reports exist in that grid cell within T hours, else 0) OR Regression (Number of reports severity weighted).

---

## 5. Machine Learning Models

### Model A: Spatiotemporal Risk Prediction (Tabular)
*   **Type:** Gradient Boosted Decision Trees (**XGBoost** or **CatBoost**). 
*   **Why:** Excellent handling of mixed feature types, interpretable feature importance, and robust to outliers.
*   **Input:** Grid cell features + Weather features.
*   **Output:** Risk Score (0-1).

### Model B: Hotspot Clustering (Unsupervised)
*   **Type:** **DBSCAN** (Density-Based Spatial Clustering of Applications with Noise).
*   **Why:** Unlike K-Means, DBSCAN does not require specifying the number of clusters and can find arbitrarily shaped clusters (e.g., following a road or low-lying area).
*   **Input:** High-risk grid cell coordinates ($lat, lng$) from Model A.
*   **Output:** Polygon boundaries or centroids of hotspots.

---

## 6. Training Strategy

*   **Offline Training:**
    *   Train initially on historical data (last 2-3 years if available, otherwise synthetic history based on topography + simulated rain events).
    *   **Retraining Frequency:** Weekly or Monthly ( as new reports accumulate).
*   **Validation:**
    *   **Time-based Split:** Train on Jan-Sept, Test on Oct-Dec (simulate future prediction).
    *   **Spatial Split:** Train on North Delhi, Test on South Delhi (test generalization).

---

## 7. Evaluation Metrics

*   **Precision (Crucial):** If we predict a hotspot, is it actually waterlogged? (Minimize false alarms to avoid authority fatigue).
*   **Recall:** Did we catch major flooding events?
*   **F1-Score:** Harmonic balance for tuning.
*   **Spatial Accuracy:** Mean distance between predicted hotspot center and actual report cluster centroid.

**Realistic Targets:**
*   Precision > 75%
*   Recall > 60% (User reports are sparse, so recall might be naturally lower).

---

## 8. Hotspot Generation Logic

1.  **Grid Prediction:** Run Model A on the entire Delhi grid using current weather forecast.
2.  **Filter:** Select cells with `Risk Score > 0.7`.
3.  **Clustering:** Apply DBSCAN (`eps=200m`, `min_samples=3`) on these cells.
4.  **Entity Creation:** 
    *   For each cluster, calculate the `centroid`.
    *   Assign a name via Reverse Geocoding (e.g., "Near Minto Road").
    *   Calculate composite severity (Max or Avg of cell risks).
5.  **Persistence:**
    *   Hotspots are active for X hours.
    *   If risk drops below threshold, mark status as 'Receding' then 'Resolved'.

---

## 9. Backend Integration

The current Node.js backend will treat the ML system as a "Microservice" or a "Worker".

**Architecture:**
*   **ML Service (Python):** A scheduled script (e.g., running via GitHub Actions, Cron, or a Celery worker).
*   **Integration Point:** The Shared Database (Supabase).

**Workflow:**
1.  **Python Script** runs every hour.
2.  Fetches weather -> Runs Mode -> Generates Hotspots.
3.  **Writes** directly to the `hotspots` table (truncating old automated entries or updating statuses).
4.  **Node.js API** (`GET /api/hotspots`) simply reads the updated table. No changes needed to the Node API code for reading.

---

## 10. Data Seeding & Setup

To execute this plan, the following setup is required.

**Python Requirements (`ml_requirements.txt`):**
```
pandas
numpy
scikit-learn
xgboost
geopandas
requests
sqlalchemy
psycopg2-binary
openmeteo-requests
```

**Step 1: Database Migration**
Add columns to `hotspots` to distinguish manual from automated entries.
```sql
ALTER TABLE hotspots ADD COLUMN source VARCHAR(20) DEFAULT 'manual'; -- 'manual' or 'ai_predicted'
ALTER TABLE hotspots ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

**Step 2: Seed Training Data (Hypothetical Command)**
```bash
# This script will download 2 years of Delhi rainfall data and generate synthetic reports
# based on low elevation points to bootstrap the model.
python3 scripts/seed_ml_data.py --years 2 --location "Delhi"
```

**Step 3: Initial Training**
```bash
python3 scripts/train_model.py --output models/waterlogging_v1.pkl
```

**Step 4: Run Inference (Scheduled)**
```bash
python3 scripts/update_hotspots.py
```

---

## 11. Scalability & Future Improvements

*   **Scalability:** The grid approach scales linearly with area. For all of India, use S2 Geometry (Google's spatial indexing) for faster lookups than H3/Lat-Lng.
*   **Computer Vision:** Allow users to upload video. Use CNNs (ResNet/EfficientNet) to estimate water depth relative to car tires or curbs.
*   **IoT Integration:** Integrate real water-level sensors (ultrasonic sensors) installed at key underpasses (e.g., Minto Bridge) as "hard" ground truth features.
