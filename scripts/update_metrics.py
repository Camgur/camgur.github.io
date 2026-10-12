import json
import os
import requests

# Replace with your actual ChemRxiv DOI
DOI = "10.26434/chemrxiv.15002480"

def fetch_metrics():
    # Querying the public Altmetric API which aggregates real-time ChemRxiv counts
    url = f"https://altmetric.com{DOI}"
    response = requests.get(url)
    
    if response.status_status == 200:
        data = response.json()
        
        # Safely extract views, downloads, or alternative metric counts
        metrics = {
            "doi": DOI,
            "views": data.get("history", {}).get("total", 0),  # Example mapping
            "score": data.get("score", 0),
            "updated_at": data.get("added_on", "")
        }
        
        # Ensure the data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save to a static file that your GitHub page can access
        with open("data/metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)
        print("Metrics successfully updated!")
    else:
        print(f"Failed to fetch metrics. Status code: {response.status_code}")

if __name__ == "__main__":
    fetch_metrics()
