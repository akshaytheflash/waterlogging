import psycopg2
import sys

DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def migrate():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Connected to database...")

        # Add 'radius' column to hotspots if it doesn't exist
        print("Checking 'radius' column in hotspots...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='hotspots' AND column_name='radius') THEN 
                    ALTER TABLE hotspots ADD COLUMN radius INTEGER DEFAULT 500; 
                    RAISE NOTICE 'Added radius column';
                END IF; 
            END $$;
        """)

        conn.commit()
        print("Migration successful! Added 'radius' column.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
