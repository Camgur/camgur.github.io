import json
import os
import requests

# Your specific ChemRxiv preprint ID
PREPRINT_ID = "15002480"

def fetch_metrics():
    # Querying the official ChemRxiv API directly for your preprint item
    url = f"https://chemrxiv.org{PREPRINT_ID}"
    
    print(f"Requesting data from: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # ChemRxiv groups metrics under public article details
        metrics = {
            "id": PREPRINT_ID,
            "views": data.get("public_views", 0),
            "downloads": data.get("public_downloads", 0),
            "doi": data.get("doi", "10.26434/chemrxiv.15002480")
        }
        
        os.makedirs("data", exist_ok=True)
        with open("data/metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)
        print(f"Success! Views: {metrics['views']}, Downloads: {metrics['downloads']}")
    else:
        print(f"Failed to fetch metrics. API Status Code: {response.status_code}")
        # Safeguard fallback file so your index.html page renders gracefully
        os.makedirs("data", exist_ok=True)
        fallback = {"id": PREPRINT_ID, "views": "Verification pending", "downloads": "Verification pending"}
        with open("data/metrics.json", "w") as f:
            json.dump(fallback, f, indent=4)

if __name__ == "__main__":
    fetch_metrics()
