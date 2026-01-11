import pandas as pd

try:
    df = pd.read_csv("india_flood_inventory.csv", encoding='latin1') # Common for these datasets
    print("Columns:", df.columns.tolist())
    
    # Filter for Delhi
    # Column names might vary, so I'll check first. But assuming 'State' or 'District'
    # I'll print unique States first if found
    
    delhi_data = df[df.astype(str).apply(lambda x: x.str.contains('Delhi', case=False, na=False)).any(axis=1)]
    
    if not delhi_data.empty:
        print(f"\nFound {len(delhi_data)} rows mentioning Delhi.")
        print(delhi_data.iloc[0].to_string()) # Print first row Series
        
        # Check if we have Lat/Lng
        possible_lat = [c for c in df.columns if 'lat' in c.lower()]
        possible_lng = [c for c in df.columns if 'lon' in c.lower() or 'lng' in c.lower()]
        print(f"\nPossible Lat/Lng cols: {possible_lat}, {possible_lng}")
    else:
        print("No Delhi data found.")
        
except Exception as e:
    print(e)
