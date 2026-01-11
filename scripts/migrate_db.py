import psycopg2
import sys

# Database connection string from server/db.js
# Note: In a production env, use environment variables.
DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def migrate():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Connected to database...")

        # Add 'source' column to hotspots if it doesn't exist
        print("Checking 'source' column in hotspots...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='hotspots' AND column_name='source') THEN 
                    ALTER TABLE hotspots ADD COLUMN source VARCHAR(20) DEFAULT 'manual'; 
                    RAISE NOTICE 'Added source column';
                END IF; 
            END $$;
        """)

        # Add 'last_updated' column to hotspots if it doesn't exist
        print("Checking 'last_updated' column in hotspots...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='hotspots' AND column_name='last_updated') THEN 
                    ALTER TABLE hotspots ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP; 
                END IF; 
            END $$;
        """)
        
        # Create 'ml_predictions' table for raw risk scores (optional but good for history)
        print("Creating 'ml_predictions' table if not exists...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id SERIAL PRIMARY KEY,
                lat DECIMAL(10, 8) NOT NULL,
                lng DECIMAL(11, 8) NOT NULL,
                risk_score FLOAT NOT NULL,
                prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("Migration successful!")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
