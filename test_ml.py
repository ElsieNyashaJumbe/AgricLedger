"""
Test script for ML model and weather service
"""

import json
from backend.weather_service import weather_service
from models.crop_suitability_model import crop_model

def test_weather():
    """Test weather service"""
    print("[TEST] Testing Weather Service...")
    
    # Test current weather
    print("\n[LOCATION] Current Weather (Harare):")
    weather = weather_service.get_current_weather('Harare')
    print(json.dumps(weather, indent=2))
    
    # Test forecast
    print("\n[FORECAST] 7-Day Forecast (Harare):")
    forecast = weather_service.get_7_day_forecast('Harare')
    if forecast.get('success'):
        for day in forecast.get('forecast', [])[:3]:
            print(f"  {day['date']}: {day['avg_temp']:.1f}°C, {day['weather']}")
    else:
        print("  Using mock data...")
        mock = weather_service.get_mock_forecast('Harare')
        for day in mock.get('forecast', [])[:3]:
            print(f"  {day['date']}: {day['avg_temp']:.1f}°C, {day['weather']}")

def test_crop_model():
    """Test crop suitability model"""
    print("\n[TEST] Testing Crop Suitability Model...")
    
    # Test location: Binga
    location = 'Binga'
    weather_data = {'temperature': 28, 'rainfall': 500, 'altitude': 500}
    
    print(f"\n[LOCATION] Location: {location}")
    print(f"[DATA] Weather: {weather_data}")
    
    predictions = crop_model.predict_suitability(
        location=location,
        weather_data=weather_data,
        soil_type='Sandy',
        soil_ph=6.0
    )
    
    print("\n[RECOMMENDATIONS] Top 5 Recommended Crops:")
    for i, pred in enumerate(predictions[:5]):
        print(f"  {i+1}. {pred['crop']}: {pred['suitability_score']:.2%} suitability")
        print(f"     Temp: {pred['temperature']:.1f}°C, Rainfall: {pred['rainfall']:.0f}mm")
        if 'explanations' in pred:
            print("     Explanations:")
            for exp in pred['explanations']:
                print(f"       {exp}")

if __name__ == "__main__":
    test_weather()
    test_crop_model()