import requests

url = "https://zenodo.org/records/16994648/files/India_Flood_Inventory_v3.csv?download=1"
try:
    print(f"Downloading from {url}...")
    r = requests.get(url)
    r.raise_for_status()
    with open("india_flood_inventory.csv", "wb") as f:
        f.write(r.content)
    print("Download successful.")
except Exception as e:
    print(f"Error: {e}")
