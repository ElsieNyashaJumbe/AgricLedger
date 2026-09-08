"""
CROP SUITABILITY MODEL TRAINING SCRIPT
AgricLedger - Zimbabwe Crop Suitability Predictor
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STEP 1: LOAD THE DATA
# ============================================================

print("=" * 60)
print("🌾 AGRICLEDGER - CROP SUITABILITY MODEL TRAINING")
print("=" * 60)
print("\n📂 Loading dataset...")

# Load the CSV file
df = pd.read_csv('zimbabwe_crop_suitability_5000.csv')

print(f"✅ Loaded {len(df)} records")
print(f"📊 Columns: {df.columns.tolist()}")
print("\n📋 First 5 rows:")
print(df.head())

# ============================================================
# STEP 2: EXPLORE THE DATA (EDA)
# ============================================================

print("\n" + "=" * 60)
print("📊 EXPLORATORY DATA ANALYSIS")
print("=" * 60)

print(f"\n📈 Target Variable (Suitability_Score):")
print(f"   Mean: {df['Suitability_Score'].mean():.2f}")
print(f"   Min: {df['Suitability_Score'].min():.2f}")
print(f"   Max: {df['Suitability_Score'].max():.2f}")
print(f"   Std Dev: {df['Suitability_Score'].std():.2f}")

print(f"\n🌱 Crop Distribution:")
print(df['Crop_Type'].value_counts().head(10))

print(f"\n🌍 Region Distribution:")
print(df['Region'].value_counts())

print(f"\n🧪 Soil Type Distribution:")
print(df['Soil_Type'].value_counts())

# Check for missing values
print(f"\n🔍 Missing Values:")
print(df.isnull().sum())

# ============================================================
# STEP 3: FEATURE ENGINEERING
# ============================================================

print("\n" + "=" * 60)
print("🔧 FEATURE ENGINEERING")
print("=" * 60)

# Create a copy for processing
df_processed = df.copy()

# List of categorical columns to encode
categorical_cols = ['Soil_Type', 'Region', 'Natural_Region', 'Climate', 'Crop_Type', 'Season']

# Create a label encoder dictionary to save for later use
encoders = {}

print("\n🔄 Encoding categorical variables...")
for col in categorical_cols:
    le = LabelEncoder()
    df_processed[f'{col}_encoded'] = le.fit_transform(df_processed[col])
    encoders[col] = le
    print(f"   ✅ Encoded: {col} -> {len(le.classes_)} unique values")

# ============================================================
# STEP 4: SELECT FEATURES FOR TRAINING
# ============================================================

print("\n📌 Selecting features for training...")

# Features to use for prediction
feature_columns = [
    'Water_Level_Percent',
    'Soil_pH_Level',
    'Expected_Yield_t_per_ha',
    'Soil_Type_encoded',
    'Region_encoded',
    'Natural_Region_encoded',
    'Climate_encoded',
    'Crop_Type_encoded',
    'Season_encoded'
]

# Target variable
target_column = 'Suitability_Score'

print(f"\n🎯 Features ({len(feature_columns)}):")
for col in feature_columns:
    print(f"   - {col}")

print(f"\n🎯 Target: {target_column}")

# ============================================================
# STEP 5: PREPARE X (features) AND y (target)
# ============================================================

X = df_processed[feature_columns]
y = df_processed[target_column]

print(f"\n📊 Feature matrix shape: {X.shape}")
print(f"📊 Target vector shape: {y.shape}")

# ============================================================
# STEP 6: SPLIT DATA INTO TRAIN AND TEST SETS
# ============================================================

print("\n" + "=" * 60)
print("📊 DATA SPLIT")
print("=" * 60)

# Split: 80% train, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42,
    stratify=df_processed['Crop_Type']  # Ensure all crops are represented
)

print(f"\n✅ Training set: {len(X_train)} samples")
print(f"✅ Test set: {len(X_test)} samples")

# ============================================================
# STEP 7: FEATURE SCALING (Optional but helps some models)
# ============================================================

print("\n" + "=" * 60)
print("📈 FEATURE SCALING")
print("=" * 60)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✅ Features scaled to standard distribution (mean=0, std=1)")

# ============================================================
# STEP 8: TRAIN MULTIPLE MODELS AND COMPARE
# ============================================================

print("\n" + "=" * 60)
print("🤖 MODEL TRAINING & COMPARISON")
print("=" * 60)

models = {
    'Random Forest': RandomForestRegressor(
        n_estimators=100, 
        max_depth=10, 
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingRegressor(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42
    ),
    'Linear Regression': LinearRegression()
}

results = {}

for name, model in models.items():
    print(f"\n🔄 Training {name}...")
    
    # Train the model
    model.fit(X_train_scaled, y_train)
    
    # Make predictions on test set
    y_pred = model.predict(X_test_scaled)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    results[name] = {
        'model': model,
        'rmse': rmse,
        'mae': mae,
        'r2': r2
    }
    
    print(f"   ✅ RMSE: {rmse:.4f}")
    print(f"   ✅ MAE: {mae:.4f}")
    print(f"   ✅ R² Score: {r2:.4f}")

# ============================================================
# STEP 9: SELECT THE BEST MODEL
# ============================================================

print("\n" + "=" * 60)
print("🏆 BEST MODEL SELECTION")
print("=" * 60)

# Find the best model based on R² score
best_model_name = max(results, key=lambda x: results[x]['r2'])
best_model = results[best_model_name]['model']
best_r2 = results[best_model_name]['r2']

print(f"\n✅ Best Model: {best_model_name}")
print(f"   R² Score: {best_r2:.4f}")

# ============================================================
# STEP 10: CROSS-VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("🔄 CROSS-VALIDATION")
print("=" * 60)

cv_scores = cross_val_score(best_model, X_train_scaled, y_train, cv=5, scoring='r2')
print(f"\n📊 5-Fold Cross-Validation R² Scores: {cv_scores}")
print(f"   Mean: {cv_scores.mean():.4f}")
print(f"   Std: {cv_scores.std():.4f}")

# ============================================================
# STEP 11: FEATURE IMPORTANCE (For Tree-based models)
# ============================================================

print("\n" + "=" * 60)
print("⭐ FEATURE IMPORTANCE")
print("=" * 60)

if hasattr(best_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': best_model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("\n📊 Feature Importance (higher = more important):")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"   {row['Feature']}: {row['Importance']:.4f}")

# ============================================================
# STEP 12: SAVE THE MODEL AND ARTIFACTS
# ============================================================

print("\n" + "=" * 60)
print("💾 SAVING MODEL ARTIFACTS")
print("=" * 60)

# Create models directory
os.makedirs('models', exist_ok=True)

# Save the best model
joblib.dump(best_model, 'models/crop_model.pkl')
print("✅ Model saved to: models/crop_model.pkl")

# Save the scaler
joblib.dump(scaler, 'models/scaler.pkl')
print("✅ Scaler saved to: models/scaler.pkl")

# Save the label encoders
joblib.dump(encoders, 'models/label_encoders.pkl')
print("✅ Label encoders saved to: models/label_encoders.pkl")

# Save feature columns list
joblib.dump(feature_columns, 'models/feature_columns.pkl')
print("✅ Feature columns saved to: models/feature_columns.pkl")

# Save training metadata
metadata = {
    'best_model_name': best_model_name,
    'r2_score': best_r2,
    'cv_mean': cv_scores.mean(),
    'cv_std': cv_scores.std(),
    'feature_columns': feature_columns,
    'target_column': target_column,
    'n_samples': len(df),
    'categorical_columns': categorical_cols,
    'feature_importance': feature_importance.to_dict() if hasattr(best_model, 'feature_importances_') else None
}

joblib.dump(metadata, 'models/metadata.pkl')
print("✅ Metadata saved to: models/metadata.pkl")

# ============================================================
# STEP 13: TEST THE MODEL WITH A SAMPLE PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("🧪 TESTING THE MODEL")
print("=" * 60)

# Create a sample farmer input
sample_input = {
    'Water_Level_Percent': 75.0,
    'Soil_pH_Level': 6.5,
    'Expected_Yield_t_per_ha': 4.5,
    'Soil_Type': 'Loam',
    'Region': 'Mashonaland East',
    'Natural_Region': 'IIa',
    'Climate': 'Subtropical Highland',
    'Crop_Type': 'Maize',
    'Season': 'Rainy Season'
}

print("\n📋 Sample Farmer Input:")
for key, value in sample_input.items():
    print(f"   {key}: {value}")

# Encode categorical features
sample_encoded = []
for col in feature_columns:
    if col.endswith('_encoded'):
        original_col = col.replace('_encoded', '')
        if original_col in sample_input:
            value = sample_input[original_col]
            encoded_val = encoders[original_col].transform([value])[0]
            sample_encoded.append(encoded_val)
        else:
            sample_encoded.append(0)
    else:
        sample_encoded.append(sample_input.get(col, 0))

# Scale the sample
sample_scaled = scaler.transform([sample_encoded])

# Make prediction
prediction = best_model.predict(sample_scaled)[0]
print(f"\n🌱 Predicted Suitability Score: {prediction:.2f}%")

# Determine suitability label
if prediction >= 75:
    label = "Highly Suitable"
elif prediction >= 60:
    label = "Suitable"
elif prediction >= 45:
    label = "Moderately Suitable"
elif prediction >= 30:
    label = "Low Suitability"
else:
    label = "Not Suitable"

print(f"✅ Suitability Label: {label}")

# ============================================================
# STEP 14: SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)

print(f"""
📊 Model Performance Summary:
   - Best Model: {best_model_name}
   - R² Score: {best_r2:.4f}
   - Cross-Validation Mean R²: {cv_scores.mean():.4f}
   - Cross-Validation Std: {cv_scores.std():.4f}

💾 Files Saved:
   - models/crop_model.pkl (trained model)
   - models/scaler.pkl (feature scaler)
   - models/label_encoders.pkl (encoders for categorical data)
   - models/feature_columns.pkl (list of features)
   - models/metadata.pkl (training metadata)

🚀 Next Steps:
   1. The model is ready to use in your Flask app
   2. Run: python app.py
   3. Navigate to the Crop Suitability section in your dashboard
   4. Enter farmer inputs and get predictions!
""")