import pandas as pd
import psycopg2
import math

DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def import_historical_data():
    try:
        # Load Manual CSV
        # format: Name, Lat, Lng, Description
        df = pd.read_csv("delhi_hotspots_manual.csv", header=None, names=['Name', 'Lat', 'Lng', 'Description'])
        print(f"Loaded {len(df)} manual hotspots.")

        # Connect to DB
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        imported_count = 0
        
        for idx, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO hotspots (name, description, severity, lat, lng, source, radius)
                    VALUES (%s, %s, %s, %s, %s, 'historical_db', 300)
                    ON CONFLICT (name) DO NOTHING
                """, (row['Name'], row['Description'], 'Critical', float(row['Lat']), float(row['Lng'])))
                imported_count += 1
            except Exception as e:
                print(f"Skipping row {idx}: {e}")
                conn.rollback()
                
        conn.commit()
        print(f"Successfully imported {imported_count} historical hotspots.")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_historical_data()
