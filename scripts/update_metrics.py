import json
import os
import requests

# Your exact ChemRxiv DOI
DOI = "10.26434/chemrxiv.15002480"

def fetch_metrics():
    # CRITICAL: Note the precise format with a trailing slash and /v1/doi/
    url = f"https://altmetric.com{DOI}"
    
    print(f"Requesting data from: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Pull data safely from the Altmetric attention registry
        metrics = {
            "doi": DOI,
            "views": data.get("history", {}).get("total", 0),  # Public tracking data
            "score": data.get("score", 0),
            "citations": data.get("cited_by_posts_count", 0)
        }
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Write to static JSON inside your repo
        with open("data/metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)
        print("Success! metrics.json has been written.")
    else:
        print(f"Failed to fetch metrics. API Status Code: {response.status_code}")
        # Create a fallback placeholder file so your JavaScript doesn't break
        os.makedirs("data", exist_ok=True)
        fallback = {"doi": DOI, "views": "Verification pending", "score": 0, "citations": 0}
        with open("data/metrics.json", "w") as f:
            json.dump(fallback, f, indent=4)

if __name__ == "__main__":
    fetch_metrics()
