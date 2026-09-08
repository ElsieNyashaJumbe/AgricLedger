"""
Crop Suitability Model for AgricLedger
ML model that recommends suitable crops based on location, weather, and 7-day forecast
Supports both trained ML model and fallback rule-based system
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CropSuitabilityModel:
    """
    Machine Learning model for crop suitability prediction
    Uses Random Forest to predict suitability scores for different crops
    Supports both trained model and fallback rule-based system
    """
    
    def __init__(self, model_path: str = 'models/crop_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.encoders = None
        self.feature_columns = None
        self.label_encoders = {}
        
        # Fallback feature columns (used if trained model not available)
        self.fallback_feature_columns = [
            'temperature', 'rainfall', 'soil_ph', 'altitude',
            'region_encoded', 'soil_type_encoded', 'forecast_temp'
        ]
        
        self.crops = ['Maize', 'Tobacco', 'Wheat', 'Soybean', 'Cotton', 
                      'Groundnuts', 'Sorghum', 'Sunflower', 'SweetPotato', 'Cassava']
        
        # Crop care instructions database
        self.crop_instructions = self._build_crop_instructions()
        
        # Try to load trained model, fallback to train or rule-based
        self.load_or_train()
    
    def load_or_train(self):
        """Load trained model if exists, otherwise train or use fallback"""
        if os.path.exists(self.model_path):
            try:
                self.load_trained_model()
                logger.info(f"✅ Trained model loaded from {self.model_path}")
                return
            except Exception as e:
                logger.error(f"Error loading trained model: {e}")
                logger.info("Attempting to train new model...")
                self.train_model()
        else:
            logger.info("No existing model found. Training new model...")
            self.train_model()
    
    def load_trained_model(self):
        """
        Load the trained model from disk
        This is the method you requested to add
        """
        import joblib
        
        # Load the trained model
        self.model = joblib.load('models/crop_model.pkl')
        logger.info("✅ Model loaded from models/crop_model.pkl")
        
        # Load the scaler
        self.scaler = joblib.load('models/scaler.pkl')
        logger.info("✅ Scaler loaded from models/scaler.pkl")
        
        # Load the label encoders
        self.encoders = joblib.load('models/label_encoders.pkl')
        logger.info("✅ Label encoders loaded from models/label_encoders.pkl")
        
        # Load feature columns
        self.feature_columns = joblib.load('models/feature_columns.pkl')
        logger.info("✅ Feature columns loaded from models/feature_columns.pkl")
        
        # Load metadata if available
        try:
            self.metadata = joblib.load('models/metadata.pkl')
            logger.info(f"✅ Metadata loaded - Best model: {self.metadata.get('best_model_name', 'Unknown')}")
        except:
            self.metadata = None
        
        logger.info("✅ Trained model loaded successfully!")
    
    def train_model(self):
        """
        Train the crop suitability model using the 5000-record dataset
        """
        try:
            # Check for the large dataset first
            large_data_path = 'zimbabwe_crop_suitability_5000.csv'
            data_path = 'data/crop_suitability_data.csv'
            
            if os.path.exists(large_data_path):
                logger.info(f"Loading dataset from {large_data_path} (5000 records)...")
                data = pd.read_csv(large_data_path)
            elif os.path.exists(data_path):
                logger.info(f"Loading dataset from {data_path}...")
                data = pd.read_csv(data_path)
            else:
                logger.warning("Training data not found. Using mock data.")
                data = self._generate_mock_training_data()
            
            # Preprocess and train
            X, y, encoders = self._preprocess_data_with_encoders(data)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"✅ Model trained successfully!")
            logger.info(f"   MSE: {mse:.4f}")
            logger.info(f"   R² Score: {r2:.4f}")
            
            # Save model artifacts
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, 'models/scaler.pkl')
            joblib.dump(encoders, 'models/label_encoders.pkl')
            
            # Store for later use
            self.encoders = encoders
            self.feature_columns = X.columns.tolist()
            joblib.dump(self.feature_columns, 'models/feature_columns.pkl')
            
            logger.info(f"✅ Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            self._create_fallback_model()
    
    def _preprocess_data_with_encoders(self, data: pd.DataFrame) -> tuple:
        """
        Preprocess data and return encoders for later use
        """
        encoders = {}
        
        # Map column names from the 5000-record dataset to expected format
        # This handles the different column naming conventions
        column_mapping = {
            'Soil_Type': 'soil_type',
            'Region': 'region',
            'Natural_Region': 'natural_region',
            'Climate': 'climate',
            'Crop_Type': 'crop',
            'Season': 'season',
            'Water_Level_Percent': 'water_level',
            'Soil_pH_Level': 'soil_ph',
            'Expected_Yield_t_per_ha': 'yield',
            'Suitability_Score': 'suitability_score'
        }
        
        # Rename columns if they exist
        for old, new in column_mapping.items():
            if old in data.columns and new not in data.columns:
                data = data.rename(columns={old: new})
        
        # Encode categorical columns
        categorical_cols = ['region', 'soil_type', 'natural_region', 'climate', 'crop', 'season']
        for col in categorical_cols:
            if col in data.columns:
                le = LabelEncoder()
                data[f'{col}_encoded'] = le.fit_transform(data[col].astype(str))
                encoders[col] = le
        
        # Build feature matrix
        features = {}
        
        # Add numerical features
        if 'water_level' in data.columns:
            features['temperature'] = data['water_level'] / 100 * 30 + 10  # Approximate conversion
        else:
            features['temperature'] = 25  # Default
        
        if 'water_level' in data.columns:
            features['rainfall'] = data['water_level'] / 100 * 1500 + 200
        else:
            features['rainfall'] = 600
        
        if 'soil_ph' in data.columns:
            features['soil_ph'] = data['soil_ph']
        else:
            features['soil_ph'] = 6.5
        
        features['altitude'] = 1000  # Default altitude
        
        # Add encoded features
        for col in ['region_encoded', 'soil_type_encoded']:
            if col in data.columns:
                features[col] = data[col]
            else:
                features[col] = 0
        
        # Add crop encoded
        if 'crop_encoded' in data.columns:
            features['crop_encoded'] = data['crop_encoded']
        elif 'crop' in data.columns:
            le = LabelEncoder()
            features['crop_encoded'] = le.fit_transform(data['crop'].astype(str))
            encoders['crop'] = le
        
        # Add forecast temperature (use current temp as proxy)
        features['forecast_temp'] = features['temperature']
        
        X = pd.DataFrame(features)
        
        # Target
        if 'suitability_score' in data.columns:
            y = data['suitability_score']
        else:
            # If no suitability score, generate from rules
            y = self._generate_scores_from_rules(data)
        
        return X, y, encoders
    
    def _generate_scores_from_rules(self, data: pd.DataFrame) -> pd.Series:
        """Generate suitability scores based on rules (fallback)"""
        scores = []
        for idx, row in data.iterrows():
            score = 0.5
            crop = row.get('crop', 'Maize')
            water = row.get('water_level', 50)
            ph = row.get('soil_ph', 6.5)
            
            if crop in self.rules:
                rules = self.rules[crop]
                if rules['temp'][0] <= 25 <= rules['temp'][1]:
                    score += 0.15
                if rules['rainfall'][0] <= water * 15 <= rules['rainfall'][1]:
                    score += 0.15
                if rules['ph'][0] <= ph <= rules['ph'][1]:
                    score += 0.15
            
            scores.append(min(1.0, max(0.0, score)))
        
        return pd.Series(scores)
    
    def _preprocess_data(self, data: pd.DataFrame) -> tuple:
        """
        Legacy preprocessing method for compatibility
        """
        for col in ['region', 'soil_type']:
            le = LabelEncoder()
            data[f'{col}_encoded'] = le.fit_transform(data[col])
            self.label_encoders[col] = le
        
        crop_encoder = LabelEncoder()
        crop_encoded = crop_encoder.fit_transform(data['crop'])
        
        X = pd.DataFrame({
            'temperature': (data['temperature_min'] + data['temperature_max']) / 2,
            'rainfall': (data['rainfall_min'] + data['rainfall_max']) / 2,
            'soil_ph': (data['soil_ph_min'] + data['soil_ph_max']) / 2,
            'altitude': (data['altitude_min'] + data['altitude_max']) / 2,
            'region_encoded': data['region_encoded'],
            'soil_type_encoded': data['soil_type_encoded'],
            'crop_encoded': crop_encoded
        })
        
        y = data['suitability_score']
        
        return X, y
    
    def _generate_mock_training_data(self) -> pd.DataFrame:
        """Generate mock training data for fallback training"""
        logger.info("Generating mock training data...")
        
        crops = ['Maize', 'Tobacco', 'Wheat', 'Soybean', 'Cotton', 
                 'Groundnuts', 'Sorghum', 'Sunflower', 'SweetPotato', 'Cassava']
        regions = ['Lowveld', 'Midveld', 'Highveld']
        soil_types = ['Sandy', 'Loam', 'Clay']
        
        data = []
        np.random.seed(42)
        
        for crop in crops:
            for region in regions:
                for soil in soil_types:
                    if crop == 'Maize':
                        temp = np.random.uniform(18, 30)
                        rainfall = np.random.uniform(500, 1200)
                        ph = np.random.uniform(5.5, 7.5)
                        altitude = np.random.uniform(0, 1500)
                    elif crop == 'Tobacco':
                        temp = np.random.uniform(15, 28)
                        rainfall = np.random.uniform(600, 1000)
                        ph = np.random.uniform(5.0, 6.5)
                        altitude = np.random.uniform(800, 1500)
                    elif crop == 'Wheat':
                        temp = np.random.uniform(10, 25)
                        rainfall = np.random.uniform(400, 800)
                        ph = np.random.uniform(6.0, 7.5)
                        altitude = np.random.uniform(500, 1800)
                    else:
                        temp = np.random.uniform(15, 35)
                        rainfall = np.random.uniform(300, 1500)
                        ph = np.random.uniform(5.0, 8.0)
                        altitude = np.random.uniform(0, 1500)
                    
                    score = 0.5
                    if 15 <= temp <= 30:
                        score += 0.15
                    if 20 <= temp <= 25:
                        score += 0.1
                    if 500 <= rainfall <= 1200:
                        score += 0.15
                    if 600 <= rainfall <= 800:
                        score += 0.1
                    if soil in ['Loam', 'Sandy']:
                        score += 0.15
                    if region == 'Lowveld' and crop in ['Maize', 'Cotton', 'Sorghum']:
                        score += 0.1
                    elif region == 'Midveld' and crop in ['Tobacco', 'Wheat']:
                        score += 0.1
                    elif region == 'Highveld' and crop in ['Wheat', 'Maize']:
                        score += 0.1
                    
                    score += np.random.uniform(-0.05, 0.05)
                    score = max(0.3, min(0.95, score))
                    
                    data.append({
                        'crop': crop,
                        'temperature_min': temp - 5,
                        'temperature_max': temp + 5,
                        'rainfall_min': max(0, rainfall - 100),
                        'rainfall_max': rainfall + 100,
                        'soil_ph_min': max(4.0, ph - 0.5),
                        'soil_ph_max': min(8.0, ph + 0.5),
                        'altitude_min': max(0, altitude - 200),
                        'altitude_max': altitude + 200,
                        'region': region,
                        'soil_type': soil,
                        'growing_days': int(np.random.uniform(90, 160)),
                        'yield_kg_ha': int(np.random.uniform(1000, 20000)),
                        'suitability_score': score
                    })
        
        return pd.DataFrame(data)
    
    def _create_fallback_model(self):
        """Create a simple rule-based model as fallback"""
        logger.info("Creating fallback rule-based model...")
        
        self.rules = {
            'Maize': {'temp': (18, 30), 'rainfall': (500, 1200), 'ph': (5.5, 7.5)},
            'Tobacco': {'temp': (15, 28), 'rainfall': (600, 1000), 'ph': (5.0, 6.5)},
            'Wheat': {'temp': (10, 25), 'rainfall': (400, 800), 'ph': (6.0, 7.5)},
            'Soybean': {'temp': (15, 30), 'rainfall': (400, 800), 'ph': (6.0, 7.0)},
            'Cotton': {'temp': (20, 35), 'rainfall': (400, 700), 'ph': (5.5, 7.5)},
            'Groundnuts': {'temp': (18, 30), 'rainfall': (500, 1000), 'ph': (5.5, 7.0)},
            'Sorghum': {'temp': (20, 35), 'rainfall': (300, 600), 'ph': (5.5, 8.0)},
            'Sunflower': {'temp': (15, 30), 'rainfall': (400, 700), 'ph': (6.0, 7.5)},
            'SweetPotato': {'temp': (15, 28), 'rainfall': (500, 1200), 'ph': (5.5, 6.5)},
            'Cassava': {'temp': (15, 35), 'rainfall': (500, 2000), 'ph': (4.5, 6.5)}
        }
        self.model = None
    
    def _build_crop_instructions(self) -> Dict[str, Dict[str, Any]]:
        """Build crop care instructions database"""
        return {
            'Maize': {
                'planting': 'Plant seeds 3-5cm deep, spacing 25-30cm between plants. Plant during the rainy season (November-December). Ensure soil has good drainage.',
                'watering': 'Water regularly during dry spells. Maize needs about 500-800mm of water during the growing season. Critical watering periods: during tasseling and grain filling.',
                'fertilizer': 'Apply Compound D (7:14:7) at planting. Top-dress with Ammonium Nitrate 4-6 weeks after planting. Use about 200kg/ha of Compound D and 150kg/ha of Ammonium Nitrate.',
                'pests': 'Watch for Fall Armyworm, Stalk Borer, and Aphids. Use recommended pesticides or neem oil. Practice crop rotation to prevent pest buildup.',
                'harvest': 'Harvest when husks turn brown and grain is hard. Leave to dry in field for 1-2 weeks then shell and store in a dry place.',
                'soil': 'Prefers well-drained loam or sandy loam soil with pH 5.5-7.5. Add organic matter to improve soil structure.'
            },
            'Tobacco': {
                'planting': 'Plant in well-prepared beds. Seeds are sown in seedbeds then transplanted after 6-8 weeks. Space plants 60-90cm apart in rows.',
                'watering': 'Regular watering is essential. Irrigate if rainfall is insufficient. Use mulch to retain moisture and reduce disease risk.',
                'fertilizer': 'Apply Compound D at planting. Top-dress with Ammonium Nitrate 4-6 weeks after transplanting. Avoid over-fertilizing as it affects quality.',
                'pests': 'Monitor for Aphids, Cutworms, and Whiteflies. Use appropriate pesticides. Practice crop rotation and remove diseased plants.',
                'harvest': 'Harvest when leaves show color change. Pick bottom leaves first, then continue upward. Cure leaves carefully to achieve desired color and aroma.',
                'soil': 'Prefers sandy loam soil with good drainage. Optimal pH 5.0-6.5. Add lime if pH is too low.'
            },
            'Wheat': {
                'planting': 'Plant in May-June as winter crop. Sow 100-120kg seed per hectare. Plant 4-5cm deep with 15-20cm row spacing.',
                'watering': 'Requires 400-800mm of water. Critical watering during flowering and grain filling. Avoid waterlogging.',
                'fertilizer': 'Apply 200kg/ha of Compound D at planting. Top-dress with Ammonium Nitrate during tillering stage. Use balanced nutrition for good yields.',
                'pests': 'Watch for Aphids, Hessian Fly, and Rust. Use fungicides for rust control. Practice crop rotation with legumes.',
                'harvest': 'Harvest when plants turn golden brown and grains are hard. Cut and allow to dry for 3-4 days before threshing.',
                'soil': 'Prefers loam or clay loam soil. Optimal pH 6.0-7.5. Ensure good drainage to prevent root rot.'
            },
            'Soybean': {
                'planting': 'Plant in November-December. Sow 60-100kg seed per hectare. Plant 3-5cm deep with 45-60cm row spacing.',
                'watering': 'Requires 400-800mm of water. Critical watering during flowering and pod filling. Avoid waterlogging.',
                'fertilizer': 'Soybeans fix their own nitrogen. Apply 100-150kg/ha of Compound D at planting. Inoculate seeds with rhizobium bacteria.',
                'pests': 'Monitor for Aphids, Soybean Rust, and Pod Borers. Use appropriate control measures. Practice crop rotation.',
                'harvest': 'Harvest when pods turn brown and seeds rattle inside. Harvest with combine harvester or manually.',
                'soil': 'Prefers well-drained loam soil. Optimal pH 6.0-7.0. Avoid highly acidic soils.'
            },
            'Cotton': {
                'planting': 'Plant in October-November. Sow 15-20kg seed per hectare. Plant 3-5cm deep with 60-90cm row spacing.',
                'watering': 'Requires 400-700mm of water. Critical watering during flowering and boll development. Drought-resistant but benefits from irrigation.',
                'fertilizer': 'Apply 200-250kg/ha of Compound D at planting. Top-dress with Ammonium Nitrate 6-8 weeks after planting.',
                'pests': 'Monitor for Boll Weevil, Aphids, and Whiteflies. Use integrated pest management strategies. Regular scouting is essential.',
                'harvest': 'Harvest when bolls open and cotton is fluffy. Use mechanical or manual picking. Store cotton in dry conditions.',
                'soil': 'Prefers well-drained sandy loam or loam soil. Optimal pH 5.5-7.5. Good drainage is essential.'
            },
            'Groundnuts': {
                'planting': 'Plant in November-December. Sow 80-120kg seed per hectare. Plant 5-8cm deep with 30-45cm row spacing.',
                'watering': 'Requires 500-1000mm of water. Critical watering during flowering and pod development. Avoid waterlogging.',
                'fertilizer': 'Apply 100-150kg/ha of Compound D at planting. Apply gypsum at flowering stage for pod development.',
                'pests': 'Watch for Aphids and Leaf Spot diseases. Use appropriate control measures. Practice crop rotation with non-legumes.',
                'harvest': 'Harvest when leaves turn yellow and pods are mature. Lift plants and dry in field for 1-2 weeks.',
                'soil': 'Prefers well-drained sandy soil. Optimal pH 5.5-7.0. Avoid waterlogged soils.'
            },
            'Sorghum': {
                'planting': 'Plant in November-December. Sow 8-10kg seed per hectare. Plant 3-5cm deep with 60-90cm row spacing.',
                'watering': 'Drought-resistant but benefits from 300-600mm of water. Critical watering during flowering and grain filling.',
                'fertilizer': 'Apply 100-150kg/ha of Compound D at planting. Top-dress with Ammonium Nitrate 4-6 weeks after planting.',
                'pests': 'Monitor for Bird damage, Stem Borers, and Aphids. Use appropriate control measures.',
                'harvest': 'Harvest when grain is hard and moisture content is below 14%. Heads can be cut and dried for storage.',
                'soil': 'Adaptable to various soils. Prefers well-drained sandy loam. Optimal pH 5.5-8.0.'
            },
            'Sunflower': {
                'planting': 'Plant in November-December. Sow 5-8kg seed per hectare. Plant 4-6cm deep with 45-60cm row spacing.',
                'watering': 'Requires 400-700mm of water. Critical watering during flowering and seed filling. Deep-rooted, tolerates some drought.',
                'fertilizer': 'Apply 150-200kg/ha of Compound D at planting. Top-dress with Ammonium Nitrate at flowering stage.',
                'pests': 'Watch for Head Moth, Sunflower Beetle, and Fungal diseases. Use appropriate control measures.',
                'harvest': 'Harvest when flower heads turn brown and seeds are firm. Cut heads and dry before threshing.',
                'soil': 'Prefers well-drained loam soil. Optimal pH 6.0-7.5. Tolerates various soil types with good drainage.'
            },
            'SweetPotato': {
                'planting': 'Plant in November-December. Use vine cuttings (30-40cm). Plant 30-40cm spacing between plants.',
                'watering': 'Requires 500-1200mm of water. Regular watering during establishment and tuber development. Avoid waterlogging.',
                'fertilizer': 'Apply organic manure or 100-150kg/ha of Compound D. Avoid excess nitrogen which reduces tuber quality.',
                'pests': 'Monitor for Weevils and Nematodes. Use resistant varieties and crop rotation.',
                'harvest': 'Harvest 3-4 months after planting when leaves yellow. Carefully dig to avoid damaging tubers.',
                'soil': 'Prefers well-drained sandy loam soil. Optimal pH 5.5-6.5. Mounding improves drainage and tuber development.'
            },
            'Cassava': {
                'planting': 'Plant in November-December. Use stem cuttings 20-30cm long. Plant 60-100cm spacing between plants.',
                'watering': 'Drought-tolerant. Requires 500-2000mm of water. Survives dry periods but yields better with adequate water.',
                'fertilizer': 'Apply organic manure or 100-150kg/ha of Compound D. Balanced nutrition improves root development.',
                'pests': 'Watch for Cassava Mosaic Virus, Mealybugs, and Mites. Use disease-free planting material.',
                'harvest': 'Harvest 8-12 months after planting. Roots can be left in ground until needed. Careful harvesting protects roots.',
                'soil': 'Prefers well-drained sandy soil. Optimal pH 4.5-6.5. Tolerates poor soils but responds well to fertilization.'
            }
        }
    
    def get_crop_instructions(self, crop: str) -> Dict[str, Any]:
        """Get care instructions for a specific crop"""
        crop_key = crop.lower().replace(' ', '')
        if crop_key in self.crop_instructions:
            return self.crop_instructions[crop_key]
        return None
    
    def predict_suitability(self, location: str, weather_data: Dict, 
                           soil_type: str = 'Loam', soil_ph: float = 6.5,
                           forecast_data: List = None) -> List[Dict]:
        """
        Predict crop suitability using trained ML model with fallback to rule-based
        
        Args:
            location: Farmer's location
            weather_data: Current weather data (temperature, rainfall, etc.)
            soil_type: Type of soil
            soil_ph: Soil pH value
            forecast_data: 7-day forecast data
        
        Returns:
            List of crop suitability predictions with care instructions
        """
        try:
            # If trained model is available, use it
            if self.model is not None and self.scaler is not None and self.encoders is not None:
                return self._predict_with_trained_model(location, weather_data, soil_type, soil_ph, forecast_data)
            # Otherwise use rule-based fallback
            else:
                logger.info("Using rule-based fallback for prediction")
                return self._predict_with_rules(location, weather_data, soil_type, soil_ph, forecast_data)
                
        except Exception as e:
            logger.error(f"Error in predict_suitability: {e}")
            # Fallback to rule-based
            return self._predict_with_rules(location, weather_data, soil_type, soil_ph, forecast_data)
    
    def _predict_with_trained_model(self, location: str, weather_data: Dict,
                                   soil_type: str = 'Loam', soil_ph: float = 6.5,
                                   forecast_data: List = None) -> List[Dict]:
        """
        Predict using the trained ML model
        """
        temp = weather_data.get('temperature', 25)
        rainfall = weather_data.get('rainfall', 600)
        altitude = weather_data.get('altitude', 500)
        forecast_temp = temp
        
        # Calculate average forecast temperature if forecast data is provided
        if forecast_data:
            forecast_temps = [day.get('avg_temp', temp) for day in forecast_data[:7] if 'avg_temp' in day]
            if forecast_temps:
                forecast_temp = sum(forecast_temps) / len(forecast_temps)
        
        # Get region
        region = self._get_region(location)
        region_mapping = {'Lowveld': 0, 'Midveld': 1, 'Highveld': 2}
        region_encoded = region_mapping.get(region, 0)
        
        # Get soil type encoding
        soil_mapping = {'Sandy': 0, 'Loam': 1, 'Clay': 2}
        soil_encoded = soil_mapping.get(soil_type, 1)
        
        predictions = []
        
        # Get list of crops from encoders if available
        crops = self.crops
        if 'crop' in self.encoders:
            crops = self.encoders['crop'].classes_.tolist()
        
        for crop in crops:
            try:
                # Encode crop
                if 'crop' in self.encoders:
                    crop_encoded = self.encoders['crop'].transform([crop])[0]
                else:
                    # Fallback: use index mapping
                    crop_encoded = self.crops.index(crop) if crop in self.crops else 0
                
                # Build feature vector
                features = {
                    'temperature': temp,
                    'rainfall': rainfall,
                    'soil_ph': soil_ph,
                    'altitude': altitude,
                    'region_encoded': region_encoded,
                    'soil_type_encoded': soil_encoded,
                    'forecast_temp': forecast_temp,
                    'crop_encoded': crop_encoded
                }
                
                # Ensure we have all required features
                if self.feature_columns:
                    # Create ordered feature array
                    feature_array = []
                    for col in self.feature_columns:
                        if col in features:
                            feature_array.append(features[col])
                        elif col == 'crop_encoded':
                            feature_array.append(crop_encoded)
                        else:
                            feature_array.append(0)
                    
                    # Scale and predict
                    scaled_features = self.scaler.transform([feature_array])
                    score = self.model.predict(scaled_features)[0]
                else:
                    # Fallback if feature columns not available
                    feature_array = [[temp, rainfall, soil_ph, altitude, region_encoded, soil_encoded, forecast_temp]]
                    scaled_features = self.scaler.transform(feature_array)
                    score = self.model.predict(scaled_features)[0]
                
                # Normalize score to 0-100
                score = max(0, min(100, score * 100))
                
                instructions = self.get_crop_instructions(crop)
                
                predictions.append({
                    'crop': crop,
                    'suitability_score': score / 100,
                    'temperature': temp,
                    'rainfall': rainfall,
                    'soil_ph': soil_ph,
                    'altitude': altitude,
                    'region': region,
                    'soil_type': soil_type,
                    'forecast_temperature': round(forecast_temp, 1),
                    'instructions': instructions
                })
                
            except Exception as e:
                logger.error(f"Error predicting for crop {crop}: {e}")
                continue
        
        # Sort by suitability score (highest first)
        predictions.sort(key=lambda x: x['suitability_score'], reverse=True)
        return predictions
    
    def _predict_with_rules(self, location: str, weather_data: Dict,
                           soil_type: str = 'Loam', soil_ph: float = 6.5,
                           forecast_data: List = None) -> List[Dict]:
        """
        Predict using rule-based fallback system
        """
        # Ensure rules exist
        if not hasattr(self, 'rules'):
            self._create_fallback_model()
        
        temp = weather_data.get('temperature', 25)
        rainfall = weather_data.get('rainfall', 600)
        altitude = weather_data.get('altitude', 500)
        forecast_temp = temp
        
        if forecast_data:
            forecast_temps = [day.get('avg_temp', temp) for day in forecast_data[:7] if 'avg_temp' in day]
            if forecast_temps:
                forecast_temp = sum(forecast_temps) / len(forecast_temps)
        
        region = self._get_region(location)
        predictions = []
        
        for crop, rules in self.rules.items():
            score = 0
            
            if rules['temp'][0] <= temp <= rules['temp'][1]:
                score += 0.25
            
            if rules['rainfall'][0] <= rainfall <= rules['rainfall'][1]:
                score += 0.20
            
            if rules['ph'][0] <= soil_ph <= rules['ph'][1]:
                score += 0.15
            
            if rules['temp'][0] <= forecast_temp <= rules['temp'][1]:
                score += 0.10
            
            if crop in ['Maize', 'Cotton', 'Sorghum'] and region == 'Lowveld':
                score += 0.10
            elif crop in ['Tobacco', 'Wheat'] and region == 'Midveld':
                score += 0.10
            elif crop in ['Wheat', 'Maize'] and region == 'Highveld':
                score += 0.10
            
            if soil_type in ['Loam', 'Sandy']:
                score += 0.10
            
            instructions = self.get_crop_instructions(crop)
            
            predictions.append({
                'crop': crop,
                'suitability_score': max(0, min(1, score)),
                'temperature': temp,
                'rainfall': rainfall,
                'soil_ph': soil_ph,
                'altitude': altitude,
                'region': region,
                'soil_type': soil_type,
                'forecast_temperature': round(forecast_temp, 1),
                'instructions': instructions
            })
        
        predictions.sort(key=lambda x: x['suitability_score'], reverse=True)
        return predictions
    
    def _get_region(self, location: str) -> str:
        """Determine region based on location"""
        highveld = ['Harare', 'Chinhoyi', 'Marondera']
        lowveld = ['Masvingo', 'Binga', 'Murehwa']
        midveld = ['Gweru', 'Kwekwe', 'Bulawayo', 'Mutare']
        
        if location in highveld:
            return 'Highveld'
        elif location in lowveld:
            return 'Lowveld'
        elif location in midveld:
            return 'Midveld'
        else:
            return 'Midveld'
    
    def _encode_region(self, region: str) -> int:
        return {'Lowveld': 0, 'Midveld': 1, 'Highveld': 2}.get(region, 0)
    
    def _encode_soil_type(self, soil_type: str) -> int:
        return {'Sandy': 0, 'Loam': 1, 'Clay': 2}.get(soil_type, 1)


# Create singleton instance
crop_model = CropSuitabilityModel()