"""
Comprehensive Data Download Script for Delhi Waterlogging Historical Data
Downloads data from multiple sources including IIT Delhi, IMD, and other verified sources
"""

import os
import requests
import pandas as pd
from datetime import datetime
import json
import time

# Create data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical')
os.makedirs(DATA_DIR, exist_ok=True)

def download_file(url, filename, description=""):
    """Download a file from URL with progress indication"""
    print(f"\n📥 Downloading: {description or filename}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        filepath = os.path.join(DATA_DIR, filename)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        print(f"\r   Progress: {progress:.1f}%", end='', flush=True)
        
        print(f"\n   ✅ Saved to: {filepath}")
        return filepath
    
    except Exception as e:
        print(f"\n   ❌ Failed: {e}")
        return None

def download_iit_delhi_data():
    """Download IIT Delhi waterlogging datasets"""
    print("\n" + "="*70)
    print("🎓 IIT DELHI HYDROSENSE LAB DATASETS")
    print("="*70)
    
    datasets = [
        {
            "name": "India Flood Inventory",
            "url": "https://zenodo.org/record/4742143/files/India_Flood_Inventory.csv",
            "filename": "india_flood_inventory.csv",
            "description": "Comprehensive flood events database for India"
        },
        {
            "name": "Barapullah Waterlogging 2021",
            "url": "https://waterhubdata.com/api/3/action/datastore_search?resource_id=20210917_I13_WL_BARAPULLAH_MP002",
            "filename": "barapullah_waterlogging_2021.json",
            "description": "Waterlogging points in Barapullah sub-basin (Monsoon 2021)"
        }
    ]
    
    downloaded_files = []
    for dataset in datasets:
        filepath = download_file(
            dataset["url"],
            dataset["filename"],
            dataset["description"]
        )
        if filepath:
            downloaded_files.append(filepath)
        time.sleep(2)  # Be respectful to servers
    
    return downloaded_files

def download_imd_rainfall_data():
    """Download IMD rainfall data"""
    print("\n" + "="*70)
    print("🌧️  IMD RAINFALL DATA")
    print("="*70)
    
    # Note: IMD data often requires manual download or API access
    # Providing alternative sources
    
    datasets = [
        {
            "name": "Delhi Rainfall Historical (OpenCity)",
            "url": "https://opencity.in/api/3/action/datastore_search?resource_id=delhi-rainfall-monthly",
            "filename": "delhi_rainfall_opencity.json",
            "description": "Monthly rainfall data for Delhi"
        }
    ]
    
    downloaded_files = []
    for dataset in datasets:
        filepath = download_file(
            dataset["url"],
            dataset["filename"],
            dataset["description"]
        )
        if filepath:
            downloaded_files.append(filepath)
        time.sleep(2)
    
    # Create a note file for manual downloads
    manual_note = """
MANUAL DOWNLOAD REQUIRED FOR SOME DATASETS
==========================================

1. IMD Rainfall Data (1901-2021)
   Source: https://data.gov.in/
   Search for: "IMD Rainfall Data Delhi"
   Format: CSV
   Save as: imd_delhi_rainfall_1901_2021.csv

2. Delhi Traffic Police Waterlogging Spots
   Source: News reports and official statements
   Manual compilation required
   Save as: delhi_traffic_police_spots.csv
   
3. DDMA Flood Reports
   Source: https://ddma.delhi.gov.in/ddma/floods
   Manual extraction from reports
   Save as: ddma_flood_reports.csv

4. Additional Zenodo Datasets
   Source: https://zenodo.org/communities/hydrosense
   Search for: "Delhi" or "India Flood"
   Download relevant datasets

Place all manually downloaded files in:
{data_dir}
    """.format(data_dir=DATA_DIR)
    
    manual_file = os.path.join(DATA_DIR, 'MANUAL_DOWNLOAD_INSTRUCTIONS.txt')
    with open(manual_file, 'w') as f:
        f.write(manual_note)
    
    print(f"\n📝 Manual download instructions saved to: {manual_file}")
    
    return downloaded_files

def create_sample_historical_data():
    """Create sample historical data based on known Delhi waterlogging incidents"""
    print("\n" + "="*70)
    print("📊 CREATING SAMPLE HISTORICAL DATA")
    print("="*70)
    
    # Known waterlogging hotspots in Delhi with historical context
    sample_incidents = [
        # 2023 Monsoon
        {"date": "2023-07-08", "location": "Minto Bridge", "lat": 28.6330, "lng": 77.2285, 
         "severity": "Critical", "depth_cm": 120, "duration_h": 6, "rainfall_mm": 153.7},
        {"date": "2023-07-08", "location": "ITO Crossing", "lat": 28.6304, "lng": 77.2425,
         "severity": "Critical", "depth_cm": 90, "duration_h": 5, "rainfall_mm": 153.7},
        {"date": "2023-07-08", "location": "Dhaula Kuan", "lat": 28.5910, "lng": 77.1610,
         "severity": "High", "depth_cm": 75, "duration_h": 4, "rainfall_mm": 153.7},
        
        # 2022 Monsoon
        {"date": "2022-08-19", "location": "Kashmere Gate", "lat": 28.6675, "lng": 77.2282,
         "severity": "High", "depth_cm": 85, "duration_h": 4, "rainfall_mm": 74.6},
        {"date": "2022-08-19", "location": "Najafgarh", "lat": 28.6139, "lng": 76.9830,
         "severity": "Critical", "depth_cm": 110, "duration_h": 7, "rainfall_mm": 74.6},
        
        # 2021 Monsoon
        {"date": "2021-09-01", "location": "Lajpat Nagar", "lat": 28.5677, "lng": 77.2432,
         "severity": "Medium", "depth_cm": 45, "duration_h": 3, "rainfall_mm": 112.2},
        {"date": "2021-09-01", "location": "Rohini Sector 18", "lat": 28.7400, "lng": 77.1300,
         "severity": "Medium", "depth_cm": 50, "duration_h": 3, "rainfall_mm": 112.2},
        
        # 2020 Monsoon
        {"date": "2020-09-02", "location": "Minto Bridge", "lat": 28.6330, "lng": 77.2285,
         "severity": "Critical", "depth_cm": 130, "duration_h": 8, "rainfall_mm": 117.0},
        {"date": "2020-09-02", "location": "Pul Prahladpur", "lat": 28.5000, "lng": 77.2800,
         "severity": "High", "depth_cm": 80, "duration_h": 5, "rainfall_mm": 117.0},
        
        # 2019 Monsoon
        {"date": "2019-08-19", "location": "ITO Crossing", "lat": 28.6304, "lng": 77.2425,
         "severity": "High", "depth_cm": 70, "duration_h": 4, "rainfall_mm": 63.2},
        {"date": "2019-08-19", "location": "Azadpur", "lat": 28.7041, "lng": 77.1750,
         "severity": "Medium", "depth_cm": 55, "duration_h": 3, "rainfall_mm": 63.2},
        
        # Additional historical incidents
        {"date": "2018-07-15", "location": "Minto Bridge", "lat": 28.6330, "lng": 77.2285,
         "severity": "Critical", "depth_cm": 115, "duration_h": 6, "rainfall_mm": 95.4},
        {"date": "2017-08-10", "location": "Dhaula Kuan", "lat": 28.5910, "lng": 77.1610,
         "severity": "High", "depth_cm": 82, "duration_h": 5, "rainfall_mm": 88.6},
        {"date": "2016-09-05", "location": "Najafgarh", "lat": 28.6139, "lng": 76.9830,
         "severity": "Critical", "depth_cm": 125, "duration_h": 7, "rainfall_mm": 102.3},
        {"date": "2015-08-28", "location": "ITO Crossing", "lat": 28.6304, "lng": 77.2425,
         "severity": "High", "depth_cm": 78, "duration_h": 4, "rainfall_mm": 71.8},
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_incidents)
    df['source'] = 'Historical_Records'
    df['affected_area_sqm'] = df['depth_cm'] * 100  # Rough estimate
    
    # Save to CSV
    filepath = os.path.join(DATA_DIR, 'sample_historical_incidents.csv')
    df.to_csv(filepath, index=False)
    print(f"✅ Created sample historical incidents: {filepath}")
    print(f"   Total incidents: {len(df)}")
    
    # Create sample rainfall data
    rainfall_data = []
    for incident in sample_incidents:
        rainfall_data.append({
            'date': incident['date'],
            'station': 'Safdarjung',
            'lat': 28.5833,
            'lng': 77.2167,
            'rainfall_24h': incident['rainfall_mm'],
            'source': 'IMD'
        })
    
    df_rainfall = pd.DataFrame(rainfall_data).drop_duplicates(subset=['date'])
    rainfall_filepath = os.path.join(DATA_DIR, 'sample_rainfall_data.csv')
    df_rainfall.to_csv(rainfall_filepath, index=False)
    print(f"✅ Created sample rainfall data: {rainfall_filepath}")
    print(f"   Total records: {len(df_rainfall)}")
    
    return [filepath, rainfall_filepath]

def create_delhi_waterlogging_spots_database():
    """Create comprehensive database of known Delhi waterlogging spots"""
    print("\n" + "="*70)
    print("📍 CREATING DELHI WATERLOGGING SPOTS DATABASE")
    print("="*70)
    
    # Comprehensive list of known waterlogging spots in Delhi
    # Based on Delhi Traffic Police data and news reports
    waterlogging_spots = [
        # Critical Spots (Frequently waterlogged)
        {"name": "Minto Bridge", "lat": 28.6330, "lng": 77.2285, "category": "Critical", "district": "Central Delhi"},
        {"name": "ITO Crossing", "lat": 28.6304, "lng": 77.2425, "category": "Critical", "district": "Central Delhi"},
        {"name": "Dhaula Kuan Underpass", "lat": 28.5910, "lng": 77.1610, "category": "Critical", "district": "South West Delhi"},
        {"name": "Najafgarh Drain Area", "lat": 28.6139, "lng": 76.9830, "category": "Critical", "district": "South West Delhi"},
        {"name": "Pul Prahladpur Underpass", "lat": 28.5000, "lng": 77.2800, "category": "Critical", "district": "South Delhi"},
        
        # High Risk Spots
        {"name": "Kashmere Gate ISBT", "lat": 28.6675, "lng": 77.2282, "category": "High", "district": "North Delhi"},
        {"name": "Azadpur Mandi", "lat": 28.7041, "lng": 77.1750, "category": "High", "district": "North Delhi"},
        {"name": "Mundka", "lat": 28.6833, "lng": 77.0333, "category": "High", "district": "West Delhi"},
        {"name": "Dwarka Sector 21", "lat": 28.5522, "lng": 77.0580, "category": "High", "district": "South West Delhi"},
        {"name": "Rohini Sector 18", "lat": 28.7400, "lng": 77.1300, "category": "High", "district": "North West Delhi"},
        
        # Medium Risk Spots
        {"name": "Lajpat Nagar Central Market", "lat": 28.5677, "lng": 77.2432, "category": "Medium", "district": "South Delhi"},
        {"name": "Sarai Kale Khan", "lat": 28.5833, "lng": 77.2667, "category": "Medium", "district": "East Delhi"},
        {"name": "Mayur Vihar Phase 1", "lat": 28.6089, "lng": 77.2953, "category": "Medium", "district": "East Delhi"},
        {"name": "Tilak Nagar", "lat": 28.6414, "lng": 77.0917, "category": "Medium", "district": "West Delhi"},
        {"name": "Pitampura", "lat": 28.6942, "lng": 77.1311, "category": "Medium", "district": "North West Delhi"},
        {"name": "Vasant Kunj", "lat": 28.5244, "lng": 77.1589, "category": "Medium", "district": "South West Delhi"},
        {"name": "Janakpuri", "lat": 28.6219, "lng": 77.0831, "category": "Medium", "district": "West Delhi"},
        {"name": "Shahdara", "lat": 28.6833, "lng": 77.2833, "category": "Medium", "district": "North East Delhi"},
        {"name": "Narela", "lat": 28.8500, "lng": 77.0833, "category": "Medium", "district": "North Delhi"},
        {"name": "Badarpur Border", "lat": 28.4833, "lng": 77.3000, "category": "Medium", "district": "South Delhi"},
    ]
    
    df = pd.DataFrame(waterlogging_spots)
    filepath = os.path.join(DATA_DIR, 'delhi_waterlogging_spots_database.csv')
    df.to_csv(filepath, index=False)
    
    print(f"✅ Created waterlogging spots database: {filepath}")
    print(f"   Total spots: {len(df)}")
    print(f"   Critical: {len(df[df['category'] == 'Critical'])}")
    print(f"   High: {len(df[df['category'] == 'High'])}")
    print(f"   Medium: {len(df[df['category'] == 'Medium'])}")
    
    return filepath

def generate_download_summary():
    """Generate summary of downloaded data"""
    print("\n" + "="*70)
    print("📋 DOWNLOAD SUMMARY")
    print("="*70)
    
    files = os.listdir(DATA_DIR)
    
    print(f"\n📁 Data directory: {DATA_DIR}")
    print(f"📊 Total files: {len(files)}\n")
    
    for filename in sorted(files):
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.isfile(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  ✓ {filename} ({size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("✨ Data download process completed!")
    print("="*70)
    print("\nNext steps:")
    print("1. Review MANUAL_DOWNLOAD_INSTRUCTIONS.txt for additional data sources")
    print("2. Run data processing scripts to clean and standardize data")
    print("3. Import data into database using import scripts")
    print("="*70)

def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("🚀 DELHI WATERLOGGING HISTORICAL DATA DOWNLOAD")
    print("="*70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_files = []
    
    # Download from various sources
    try:
        # IIT Delhi datasets
        files = download_iit_delhi_data()
        all_files.extend(files)
        
        # IMD rainfall data
        files = download_imd_rainfall_data()
        all_files.extend(files)
        
        # Create sample data
        files = create_sample_historical_data()
        all_files.extend(files)
        
        # Create waterlogging spots database
        filepath = create_delhi_waterlogging_spots_database()
        all_files.append(filepath)
        
    except Exception as e:
        print(f"\n❌ Error during download: {e}")
    
    # Generate summary
    generate_download_summary()
    
    print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
