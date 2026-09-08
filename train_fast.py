"""
FAST CROP SUITABILITY MODEL TRAINING
Quick training for Windows - 1-3 minutes
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🌾 FAST CROP SUITABILITY MODEL TRAINING")
print("=" * 60)

# Load data
print("\n📂 Loading dataset...")
df = pd.read_csv('zimbabwe_crop_suitability_5000.csv')
print(f"✅ Loaded {len(df)} records")

# Feature Engineering
print("\n🔧 Feature Engineering...")
df_processed = df.copy()

# Create simple features
df_processed['water_temp_interaction'] = (df_processed['Water_Level_Percent'] / 100) * 35
df_processed['soil_water_interaction'] = df_processed['Water_Level_Percent'] * df_processed['Soil_pH_Level'] / 100
df_processed['water_squared'] = df_processed['Water_Level_Percent'] ** 2
df_processed['ph_squared'] = df_processed['Soil_pH_Level'] ** 2

print("✅ Feature engineering complete")

# Encode categoricals
print("\n🔄 Encoding categorical variables...")
categorical_cols = ['Soil_Type', 'Region', 'Natural_Region', 'Climate', 'Crop_Type', 'Season']
encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    df_processed[f'{col}_encoded'] = le.fit_transform(df_processed[col].astype(str))
    encoders[col] = le
    print(f"   ✅ Encoded: {col} ({len(le.classes_)} unique)")

# Select features
feature_columns = [
    'Water_Level_Percent',
    'Soil_pH_Level',
    'Expected_Yield_t_per_ha',
    'water_squared',
    'ph_squared',
    'water_temp_interaction',
    'soil_water_interaction',
    'Soil_Type_encoded',
    'Region_encoded',
    'Natural_Region_encoded',
    'Climate_encoded',
    'Crop_Type_encoded',  # ← CRITICAL: Include crop!
    'Season_encoded'
]

print(f"\n📌 {len(feature_columns)} features selected")

# Prepare data
X = df_processed[feature_columns]
y = df_processed['Suitability_Score']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n✅ Training: {len(X_train)} samples")
print(f"✅ Test: {len(X_test)} samples")

# Scale
print("\n📈 Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print("✅ Features scaled")

# Train - FAST
print("\n🤖 Training Random Forest...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
r2 = r2_score(y_test, y_pred)

print(f"\n📊 Model Performance:")
print(f"   R² Score: {r2:.4f}")

# Save
print("\n💾 Saving model artifacts...")
os.makedirs('models', exist_ok=True)

joblib.dump(model, 'models/crop_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(encoders, 'models/label_encoders.pkl')
joblib.dump(feature_columns, 'models/feature_columns.pkl')

print("✅ Model saved successfully!")

# Verify
print("\n📁 Verifying saved files:")
files = ['crop_model.pkl', 'scaler.pkl', 'label_encoders.pkl', 'feature_columns.pkl']
all_ok = True
for f in files:
    path = f'models/{f}'
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"   ✅ {f} ({size:,} bytes)")
    else:
        print(f"   ❌ {f} - MISSING!")
        all_ok = False

if all_ok:
    print("\n" + "=" * 60)
    print("🎉 TRAINING COMPLETE!")
    print("=" * 60)
    print("\n✅ All model files saved successfully!")
    print("🚀 You can now run: python app.py")
else:
    print("\n❌ Some files are missing. Please check the errors above.")