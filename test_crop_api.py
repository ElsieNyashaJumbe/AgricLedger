import requests
import json

# Make sure you're logged in first - get a session cookie
# Or test without auth if you remove @login_required temporarily

# Test data
payload = {
    "location": "Matabeleland North",
    "region": "Midveld",
    "soil_type": "Sandy Soil",
    "soil_ph": 6.2,
    "climate": "Semi-Arid",
    "water_mm": 450,
    "crop_type": "Tobacco",
    "hectares": 5,
    "target_yield": 10,
    "budget": 5000,
    "capital": 3000,
    "labour": 5
}

# Since the endpoint requires login, you need to login first
# For testing, you can temporarily comment out @login_required in app.py

response = requests.post(
    "http://localhost:5000/api/crops/suitability",
    json=payload,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))