import psycopg2
import pandas as pd

DB_URL = "postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def check():
    try:
        conn = psycopg2.connect(DB_URL)
        df = pd.read_sql("SELECT name, severity, source, last_updated FROM hotspots WHERE source='ai_predicted'", conn)
        print("\n--- AI PREDICTED HOTSPOTS ---")
        if df.empty:
            print("No hotspots found.")
        else:
            print(df.to_string())
        conn.close()
    except Exception as e:
        print(e)
if __name__ == "__main__":
    check()
