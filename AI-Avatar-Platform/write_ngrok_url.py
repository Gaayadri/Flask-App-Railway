# write_ngrok_url.py
import requests
import json
import os

def fetch_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except Exception as e:
        print("Error fetching ngrok URL:", e)
    return None

ngrok_url = fetch_ngrok_url()
if ngrok_url:
    # Save to Unity's Resources folder
    unity_path = os.path.join("Assets", "Resources")
    os.makedirs(unity_path, exist_ok=True)

    config_path = os.path.join(unity_path, "ngrok_config.json")
    with open(config_path, "w") as f:
        json.dump({ "ngrok_url": ngrok_url }, f)
    print(f"✅ Ngrok URL saved to {config_path}: {ngrok_url}")
else:
    print("❌ Ngrok URL not found. Is ngrok running?")
