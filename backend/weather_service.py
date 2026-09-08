"""
Weather Service Module for AgricLedger
Fetches real-time weather data and 7-day forecasts from Visual Crossing Weather API
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service for fetching weather data and forecasts from Visual Crossing Weather API
    """
    
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY', '')
        # Visual Crossing API endpoints
        self.base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        
        # Zimbabwe major cities coordinates
        self.locations = {
            'Harare': {'lat': -17.8252, 'lon': 31.0335},
            'Bulawayo': {'lat': -20.1486, 'lon': 28.5806},
            'Mutare': {'lat': -18.9757, 'lon': 32.6706},
            'Binga': {'lat': -17.6200, 'lon': 27.3400},
            'Murehwa': {'lat': -17.6433, 'lon': 31.7833},
            'Gweru': {'lat': -19.4583, 'lon': 29.8167},
            'Masvingo': {'lat': -20.0737, 'lon': 30.8223},
            'Chinhoyi': {'lat': -17.3667, 'lon': 30.2000},
            'Kadoma': {'lat': -18.3333, 'lon': 29.9167},
            'Kwekwe': {'lat': -18.9264, 'lon': 29.8236}
        }
        
        # Check if API key is valid
        self.has_valid_api_key = bool(self.api_key) and len(self.api_key) > 10
        if self.has_valid_api_key:
            logger.info("✅ Weather API key found and validated")
        else:
            logger.warning("⚠️ No valid Weather API key found - using mock data fallback")
    
    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a location using Visual Crossing Weather API
        
        Args:
            location: City name in Zimbabwe
            
        Returns:
            Dict with current weather data
        """
        try:
            # Validate location
            if location not in self.locations:
                logger.warning(f"Location {location} not found, defaulting to Harare")
                location = 'Harare'
            
            # If no API key, return mock data immediately
            if not self.has_valid_api_key:
                logger.info(f"Using mock weather data for {location}")
                return self._get_mock_weather(location)
            
            # Build Visual Crossing API URL
            lat = self.locations[location]['lat']
            lon = self.locations[location]['lon']
            
            # Get today's weather
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/{lat},{lon}/{today}?unitGroup=metric&include=current&key={self.api_key}&contentType=json"
            
            logger.info(f"Fetching current weather for {location} from Visual Crossing...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Current weather for {location} fetched successfully")
                
                # Extract current conditions
                current = data.get('currentConditions', {})
                days = data.get('days', [{}])[0]
                
                return {
                    'success': True,
                    'location': location,
                    'temperature': current.get('temp', days.get('temp', 0)),
                    'feels_like': current.get('feelslike', days.get('feelslike', 0)),
                    'humidity': current.get('humidity', days.get('humidity', 0)),
                    'pressure': current.get('pressure', days.get('pressure', 0)),
                    'weather': current.get('conditions', days.get('conditions', 'Clear')),
                    'weather_icon': self._get_weather_icon(current.get('conditions', 'Clear')),
                    'wind_speed': current.get('windspeed', days.get('windspeed', 0)),
                    'wind_deg': current.get('winddir', 0),
                    'clouds': current.get('cloudcover', 0),
                    'sunrise': days.get('sunrise', 'N/A'),
                    'sunset': days.get('sunset', 'N/A'),
                    'timestamp': datetime.now().isoformat(),
                    'is_mock': False,
                    'weather_source': 'api'
                }
            else:
                logger.error(f"Weather API error: {response.status_code} - {response.text}")
                return self._get_mock_weather(location)
                
        except requests.exceptions.Timeout:
            logger.error("Weather API request timed out")
            return self._get_mock_weather(location)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to Weather API")
            return self._get_mock_weather(location)
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return self._get_mock_weather(location)
    
    def get_7_day_forecast(self, location: str) -> Dict[str, Any]:
        """
        Get 7-day weather forecast for a location using Visual Crossing Weather API
        
        Args:
            location: City name in Zimbabwe
            
        Returns:
            Dict with 7-day forecast data
        """
        try:
            if location not in self.locations:
                location = 'Harare'
            
            # If no API key, return mock data immediately
            if not self.has_valid_api_key:
                logger.info(f"Using mock forecast data for {location}")
                return self.get_mock_forecast(location)
            
            lat = self.locations[location]['lat']
            lon = self.locations[location]['lon']
            
            # Get 7-day forecast
            url = f"{self.base_url}/{lat},{lon}/next7days?unitGroup=metric&include=days&key={self.api_key}&contentType=json"
            
            logger.info(f"Fetching 7-day forecast for {location} from Visual Crossing...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Forecast for {location} fetched successfully")
                
                days = data.get('days', [])
                forecast = []
                
                for day in days[:7]:
                    forecast.append({
                        'date': day.get('datetime', ''),
                        'avg_temp': day.get('temp', 0),
                        'min_temp': day.get('tempmax', 0),
                        'max_temp': day.get('tempmin', 0),
                        'humidity': day.get('humidity', 0),
                        'pressure': day.get('pressure', 0),
                        'weather': day.get('conditions', 'Clear'),
                        'weather_icon': self._get_weather_icon(day.get('conditions', 'Clear')),
                        'wind_speed': day.get('windspeed', 0),
                        'rain': day.get('precip', 0)
                    })
                
                return {
                    'success': True,
                    'location': location,
                    'forecast': forecast,
                    'raw': forecast,
                    'is_mock': False,
                    'weather_source': 'api'
                }
            else:
                logger.error(f"Forecast API error: {response.status_code}")
                return self.get_mock_forecast(location)
                
        except requests.exceptions.Timeout:
            logger.error("Forecast API request timed out")
            return self.get_mock_forecast(location)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to Forecast API")
            return self.get_mock_forecast(location)
        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            return self.get_mock_forecast(location)
    
    def _get_weather_icon(self, condition: str) -> str:
        """Map weather conditions to OpenWeatherMap icon codes"""
        condition_lower = condition.lower()
        if 'sunny' in condition_lower or 'clear' in condition_lower:
            return '01d'
        elif 'partly' in condition_lower or 'cloud' in condition_lower:
            return '02d'
        elif 'overcast' in condition_lower:
            return '04d'
        elif 'rain' in condition_lower or 'shower' in condition_lower:
            return '10d'
        elif 'thunder' in condition_lower or 'storm' in condition_lower:
            return '11d'
        elif 'snow' in condition_lower:
            return '13d'
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return '50d'
        else:
            return '01d'
    
    def _get_mock_weather(self, location: str) -> Dict[str, Any]:
        """Generate mock current weather data (fallback when API fails)"""
        logger.info(f"Generating mock weather data for {location}")
        return {
            'success': True,
            'location': location,
            'temperature': 25.5,
            'feels_like': 26.0,
            'humidity': 65,
            'pressure': 1013,
            'weather': 'Partly Cloudy',
            'weather_icon': '02d',
            'wind_speed': 12,
            'wind_deg': 180,
            'clouds': 40,
            'sunrise': '06:00',
            'sunset': '18:00',
            'timestamp': datetime.now().isoformat(),
            'is_mock': True,
            'weather_source': 'synthetic_fallback'
        }
    
    def get_mock_forecast(self, location: str) -> Dict[str, Any]:
        """Get mock forecast data when API key is not available"""
        logger.info(f"Generating mock forecast for {location}")
        
        forecast = []
        start_date = datetime.now()
        
        weather_conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Clear']
        weather_icons = ['01d', '02d', '03d', '10d', '01d']
        temp_base = {
            'Harare': 22, 'Bulawayo': 20, 'Mutare': 18, 'Binga': 28,
            'Murehwa': 21, 'Gweru': 19, 'Masvingo': 23, 'Chinhoyi': 22,
            'Kadoma': 24, 'Kwekwe': 23
        }
        base_temp = temp_base.get(location, 22)
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            avg_temp = base_temp + (i % 5) - 2
            min_temp = avg_temp - 5 + (i % 3)
            max_temp = avg_temp + 5 + (i % 4)
            
            day_data = {
                'date': date.strftime('%Y-%m-%d'),
                'avg_temp': avg_temp,
                'min_temp': min_temp,
                'max_temp': max_temp,
                'avg_humidity': 55 + (i * 3) % 30,
                'weather': weather_conditions[i % 5],
                'weather_icon': weather_icons[i % 5],
                'total_rain': [0, 0, 0.5, 2.5, 0, 1.5, 3.0][i % 7]
            }
            forecast.append(day_data)
        
        return {
            'success': True,
            'location': location,
            'forecast': forecast,
            'is_mock': True,
            'weather_source': 'synthetic_fallback'
        }
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test if the API key is working properly"""
        if not self.has_valid_api_key:
            return {
                'success': False,
                'error': 'No API key found. Please set WEATHER_API_KEY in .env file'
            }
        
        try:
            # Test with Harare
            lat = self.locations['Harare']['lat']
            lon = self.locations['Harare']['lon']
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/{lat},{lon}/{today}?unitGroup=metric&include=current&key={self.api_key}&contentType=json"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': '✅ Weather API key is valid and working!',
                    'data': response.json()
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': '❌ Invalid API key. Please check your WEATHER_API_KEY in .env file'
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }


# Create singleton instance
weather_service = WeatherService()