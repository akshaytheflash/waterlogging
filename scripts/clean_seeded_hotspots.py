import psycopg2
import pandas as pd

DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def clean_hotspots():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("\n--- CLEANING HOTSPOTS ---")
        
        # 1. Delete manual hotspots (seeded ones)
        # Assuming seeded ones have default source 'manual' or NULL
        # My migrate script set default to 'manual'.
        
        cur.execute("SELECT COUNT(*) FROM hotspots WHERE source IS NULL OR source = 'manual'")
        count = cur.fetchone()[0]
        print(f"Found {count} manual/seeded hotspots.")
        
        if count > 0:
            cur.execute("DELETE FROM hotspots WHERE source IS NULL OR source = 'manual'")
            print(f"Deleted {count} seeded hotspots.")
        
        # 2. Verify what remains
        cur.execute("SELECT name, source FROM hotspots")
        remaining = cur.fetchall()
        print("\nRemaining Hotspots in DB:")
        for r in remaining:
            print(f"- {r[0]} ({r[1]})")
            
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_hotspots()
