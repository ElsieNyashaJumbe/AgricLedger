"""
Test script for AgricLedger API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    print("🏥 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_weather_current():
    print("🌤️ Testing Current Weather...")
    response = requests.get(f"{BASE_URL}/api/weather/current/Harare")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_weather_forecast():
    print("📅 Testing 7-Day Forecast...")
    response = requests.get(f"{BASE_URL}/api/weather/forecast/Harare")
    print(f"Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        for day in data.get('forecast', [])[:3]:
            print(f"  {day['date']}: {day['avg_temp']:.1f}°C, {day['weather']}")
    print()

def test_crop_suitability():
    print("🌾 Testing Crop Suitability...")
    payload = {
        "location": "Binga",
        "soil_type": "Sandy",
        "soil_ph": 6.0
    }
    response = requests.post(
        f"{BASE_URL}/api/crops/suitability",
        json=payload
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print(f"Location: {data['location']}")
        print(f"Soil Type: {data['soil_type']}")
        print(f"Soil pH: {data['soil_ph']}")
        print("\nTop 5 Recommended Crops:")
        for i, pred in enumerate(data.get('predictions', [])[:5]):
            print(f"  {i+1}. {pred['crop']}: {pred['suitability_score']:.2%} suitability")
    print()

def test_market_demand():
    print("📊 Testing Market Demand...")
    response = requests.get(f"{BASE_URL}/api/market/demand")
    print(f"Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        for market, info in data.get('markets', {}).items():
            print(f"\n📍 {market}:")
            for crop in info.get('crops_in_demand', [])[:3]:
                print(f"  - {crop['crop']}: {crop['demand']} demand, {crop['price_range']}")
    print()

def test_all_crops():
    print("🌱 Testing All Crops...")
    response = requests.get(f"{BASE_URL}/api/crops/all")
    print(f"Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print(f"Crops: {', '.join(data.get('crops', []))}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 AGRICLEDGER API TEST")
    print("=" * 50)
    test_health()
    test_weather_current()
    test_weather_forecast()
    test_crop_suitability()
    test_market_demand()
    test_all_crops()