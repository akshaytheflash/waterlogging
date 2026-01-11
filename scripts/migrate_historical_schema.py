"""
Database Migration Script for Historical Prediction System
Creates new tables for historical incidents, rainfall data, and predictions
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

def run_migration():
    """Execute database migration for historical prediction system"""
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("🚀 Starting database migration for Historical Prediction System...")
        
        # 1. Create historical_incidents table
        print("\n📊 Creating historical_incidents table...")
        cur.execute("""
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
                source VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for historical_incidents
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_incidents_date 
            ON historical_incidents(incident_date);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_incidents_location 
            ON historical_incidents(lat, lng);
        """)
        print("✅ historical_incidents table created")
        
        # 2. Create historical_rainfall table
        print("\n🌧️  Creating historical_rainfall table...")
        cur.execute("""
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
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_date, station_name)
            );
        """)
        
        # Create indexes for historical_rainfall
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_rainfall_date 
            ON historical_rainfall(record_date);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_rainfall_station 
            ON historical_rainfall(station_name);
        """)
        print("✅ historical_rainfall table created")
        
        # 3. Create predicted_hotspots table
        print("\n🎯 Creating predicted_hotspots table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predicted_hotspots (
                id SERIAL PRIMARY KEY,
                prediction_date DATE NOT NULL,
                name VARCHAR(200),
                lat DECIMAL(10, 8) NOT NULL,
                lng DECIMAL(11, 8) NOT NULL,
                severity VARCHAR(20) CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
                confidence_score DECIMAL(4, 3),
                predicted_rainfall_mm DECIMAL(6, 2),
                risk_factors TEXT,
                radius_meters INTEGER DEFAULT 200,
                model_version VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(prediction_date, lat, lng)
            );
        """)
        
        # Create indexes for predicted_hotspots
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_predicted_hotspots_date 
            ON predicted_hotspots(prediction_date);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_predicted_hotspots_location 
            ON predicted_hotspots(lat, lng);
        """)
        print("✅ predicted_hotspots table created")
        
        # 4. Create model_metadata table
        print("\n🤖 Creating model_metadata table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS model_metadata (
                id SERIAL PRIMARY KEY,
                model_version VARCHAR(50) UNIQUE NOT NULL,
                training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                training_samples INTEGER,
                accuracy DECIMAL(5, 4),
                precision_score DECIMAL(5, 4),
                recall_score DECIMAL(5, 4),
                f1_score DECIMAL(5, 4),
                feature_importance TEXT,
                hyperparameters TEXT,
                data_sources TEXT,
                notes TEXT
            );
        """)
        print("✅ model_metadata table created")
        
        # 5. Update existing hotspots table
        print("\n🔄 Updating existing hotspots table...")
        cur.execute("""
            ALTER TABLE hotspots 
            ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';
        """)
        cur.execute("""
            ALTER TABLE hotspots 
            ADD COLUMN IF NOT EXISTS prediction_date DATE;
        """)
        cur.execute("""
            ALTER TABLE hotspots 
            ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(4, 3);
        """)
        cur.execute("""
            ALTER TABLE hotspots 
            ADD COLUMN IF NOT EXISTS radius_meters INTEGER DEFAULT 200;
        """)
        cur.execute("""
            ALTER TABLE hotspots 
            ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        """)
        print("✅ hotspots table updated")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*60)
        print("✨ Migration completed successfully!")
        print("="*60)
        
        # Print summary
        print("\n📋 Summary:")
        print("  ✓ historical_incidents table created")
        print("  ✓ historical_rainfall table created")
        print("  ✓ predicted_hotspots table created")
        print("  ✓ model_metadata table created")
        print("  ✓ hotspots table updated with new columns")
        print("  ✓ All indexes created")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
