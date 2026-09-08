"""
Test the trained crop suitability model
"""

import joblib
import numpy as np
import pandas as pd

# Load the model and artifacts
model = joblib.load('models/crop_model.pkl')
scaler = joblib.load('models/scaler.pkl')
encoders = joblib.load('models/label_encoders.pkl')
feature_columns = joblib.load('models/feature_columns.pkl')

def predict_suitability(farmer_input):
    """
    Predict crop suitability for a farmer's input
    
    Args:
        farmer_input: dict with farmer's conditions
    
    Returns:
        suitability_score: float (0-100)
    """
    # Encode categorical features
    sample_encoded = []
    
    for col in feature_columns:
        if col.endswith('_encoded'):
            original_col = col.replace('_encoded', '')
            if original_col in farmer_input:
                value = farmer_input[original_col]
                # Handle if value not in encoder classes
                if value in encoders[original_col].classes_:
                    encoded_val = encoders[original_col].transform([value])[0]
                else:
                    encoded_val = 0  # Default for unknown
                sample_encoded.append(encoded_val)
            else:
                sample_encoded.append(0)
        else:
            sample_encoded.append(farmer_input.get(col, 0))
    
    # Scale and predict
    sample_scaled = scaler.transform([sample_encoded])
    prediction = model.predict(sample_scaled)[0]
    
    return max(0, min(100, prediction))  # Clamp between 0-100

# Test with different crops
test_inputs = [
    {
        'Water_Level_Percent': 75.0,
        'Soil_pH_Level': 6.5,
        'Expected_Yield_t_per_ha': 4.5,
        'Soil_Type': 'Loam',
        'Region': 'Mashonaland East',
        'Natural_Region': 'IIa',
        'Climate': 'Subtropical Highland',
        'Crop_Type': 'Maize',
        'Season': 'Rainy Season'
    },
    {
        'Water_Level_Percent': 55.0,
        'Soil_pH_Level': 5.8,
        'Expected_Yield_t_per_ha': 2.0,
        'Soil_Type': 'Sandy Soil',
        'Region': 'Matabeleland North',
        'Natural_Region': 'III',
        'Climate': 'Semi-Arid',
        'Crop_Type': 'Tobacco',
        'Season': 'Winter'
    },
    {
        'Water_Level_Percent': 85.0,
        'Soil_pH_Level': 7.0,
        'Expected_Yield_t_per_ha': 3.5,
        'Soil_Type': 'Clay Loam',
        'Region': 'Midlands',
        'Natural_Region': 'III',
        'Climate': 'Temperate Highland',
        'Crop_Type': 'Wheat',
        'Season': 'Dry Season'
    }
]

print("=" * 60)
print("🌾 TESTING CROP SUITABILITY MODEL")
print("=" * 60)

for i, farmer_input in enumerate(test_inputs, 1):
    score = predict_suitability(farmer_input)
    
    # Determine label
    if score >= 75:
        label = "Highly Suitable"
    elif score >= 60:
        label = "Suitable"
    elif score >= 45:
        label = "Moderately Suitable"
    elif score >= 30:
        label = "Low Suitability"
    else:
        label = "Not Suitable"
    
    print(f"\n📋 Test {i}:")
    print(f"   Crop: {farmer_input['Crop_Type']}")
    print(f"   Region: {farmer_input['Region']}")
    print(f"   Water: {farmer_input['Water_Level_Percent']}%")
    print(f"   pH: {farmer_input['Soil_pH_Level']}")
    print(f"   🌱 Suitability Score: {score:.1f}%")
    print(f"   ✅ Label: {label}")