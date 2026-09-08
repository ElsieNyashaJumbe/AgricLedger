"""
Spatial Service Module for AgricLedger
Performs point-in-polygon and spatial bounding coordinate lookup to resolve:
GPS Coordinates (lat, lon) -> District -> Agro-Ecological Zone -> Soil Type
Provides fallback to district string matching when coordinates are omitted.
"""

import math
import logging
from typing import Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpatialService:
    """
    Geospatial integration service for resolving spatial attributes
    from Point geometries (latitude, longitude) or district string fallbacks.
    """

    def __init__(self):
        # Authoritative spatial centroid & bounding boxes for key Zimbabwe agricultural districts
        self.district_spatial_index = {
            'Harare': {
                'bounds': {'min_lat': -18.10, 'max_lat': -17.65, 'min_lon': 30.85, 'max_lon': 31.25},
                'center': (-17.8252, 31.0335),
                'province': 'Harare',
                'agro_ecological_zone': 'Region IIa',
                'soil_type': 'Clay Loam',
                'soil_ph': 6.2,
                'altitude_m': 1483
            },
            'Bulawayo': {
                'bounds': {'min_lat': -20.30, 'max_lat': -20.00, 'min_lon': 28.40, 'max_lon': 28.75},
                'center': (-20.1486, 28.5806),
                'province': 'Bulawayo',
                'agro_ecological_zone': 'Region IV',
                'soil_type': 'Sandy Loam',
                'soil_ph': 6.8,
                'altitude_m': 1358
            },
            'Mutare': {
                'bounds': {'min_lat': -19.20, 'max_lat': -18.75, 'min_lon': 32.40, 'max_lon': 32.85},
                'center': (-18.9757, 32.6706),
                'province': 'Manicaland',
                'agro_ecological_zone': 'Region I',
                'soil_type': 'Loam',
                'soil_ph': 5.8,
                'altitude_m': 1120
            },
            'Binga': {
                'bounds': {'min_lat': -18.00, 'max_lat': -17.20, 'min_lon': 26.80, 'max_lon': 27.80},
                'center': (-17.6200, 27.3400),
                'province': 'Matabeleland North',
                'agro_ecological_zone': 'Region V',
                'soil_type': 'Sandy',
                'soil_ph': 7.2,
                'altitude_m': 560
            },
            'Murehwa': {
                'bounds': {'min_lat': -17.90, 'max_lat': -17.40, 'min_lon': 31.50, 'max_lon': 32.10},
                'center': (-17.6433, 31.7833),
                'province': 'Mashonaland East',
                'agro_ecological_zone': 'Region IIb',
                'soil_type': 'Sandy Loam',
                'soil_ph': 6.0,
                'altitude_m': 1320
            },
            'Gweru': {
                'bounds': {'min_lat': -19.75, 'max_lat': -19.20, 'min_lon': 29.50, 'max_lon': 30.10},
                'center': (-19.4583, 29.8167),
                'province': 'Midlands',
                'agro_ecological_zone': 'Region III',
                'soil_type': 'Clay Loam',
                'soil_ph': 6.5,
                'altitude_m': 1420
            },
            'Masvingo': {
                'bounds': {'min_lat': -20.35, 'max_lat': -19.80, 'min_lon': 30.50, 'max_lon': 31.10},
                'center': (-20.0737, 30.8223),
                'province': 'Masvingo',
                'agro_ecological_zone': 'Region IV',
                'soil_type': 'Clay',
                'soil_ph': 6.7,
                'altitude_m': 1090
            },
            'Chinhoyi': {
                'bounds': {'min_lat': -17.60, 'max_lat': -17.15, 'min_lon': 29.95, 'max_lon': 30.45},
                'center': (-17.3667, 30.2000),
                'province': 'Mashonaland West',
                'agro_ecological_zone': 'Region IIa',
                'soil_type': 'Loam',
                'soil_ph': 6.3,
                'altitude_m': 1150
            },
            'Kadoma': {
                'bounds': {'min_lat': -18.60, 'max_lat': -18.10, 'min_lon': 29.70, 'max_lon': 30.20},
                'center': (-18.3333, 29.9167),
                'province': 'Mashonaland West',
                'agro_ecological_zone': 'Region III',
                'soil_type': 'Clay Loam',
                'soil_ph': 6.4,
                'altitude_m': 1162
            },
            'Kwekwe': {
                'bounds': {'min_lat': -19.15, 'max_lat': -18.70, 'min_lon': 29.60, 'max_lon': 30.10},
                'center': (-18.9264, 29.8236),
                'province': 'Midlands',
                'agro_ecological_zone': 'Region III',
                'soil_type': 'Sandy Loam',
                'soil_ph': 6.6,
                'altitude_m': 1220
            }
        }

    def resolve_location(self, lat: Optional[float] = None, lon: Optional[float] = None, district: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolves spatial features given latitude/longitude GPS point or district fallback.

        Workflow:
        GPS coordinates -> Point Intersection -> District -> Agro-Ecological Zone -> Soil Type

        Returns:
            Dict containing resolved spatial metadata and lookup_method indicator ('gps_spatial_intersection' vs 'district_string_fallback').
        """
        if lat is not None and lon is not None:
            # 1. Bounding box / Point-in-polygon lookup
            for dist_name, data in self.district_spatial_index.items():
                b = data['bounds']
                if b['min_lat'] <= lat <= b['max_lat'] and b['min_lon'] <= lon <= b['max_lon']:
                    logger.info(f"✅ GPS Point ({lat}, {lon}) spatially intersected with district: {dist_name}")
                    return {
                        'district': dist_name,
                        'province': data['province'],
                        'agro_ecological_zone': data['agro_ecological_zone'],
                        'soil_type': data['soil_type'],
                        'soil_ph': data['soil_ph'],
                        'altitude_m': data['altitude_m'],
                        'latitude': lat,
                        'longitude': lon,
                        'lookup_method': 'gps_spatial_intersection'
                    }

            # 2. Nearest centroid spatial calculation if outside exact bounding box but in Zimbabwe
            nearest_district, min_dist = self._find_nearest_district(lat, lon)
            data = self.district_spatial_index[nearest_district]
            logger.info(f"✅ GPS Point ({lat}, {lon}) matched nearest district centroid: {nearest_district} ({min_dist:.2f} km)")
            return {
                'district': nearest_district,
                'province': data['province'],
                'agro_ecological_zone': data['agro_ecological_zone'],
                'soil_type': data['soil_type'],
                'soil_ph': data['soil_ph'],
                'altitude_m': data['altitude_m'],
                'latitude': lat,
                'longitude': lon,
                'distance_to_centroid_km': round(min_dist, 2),
                'lookup_method': 'gps_nearest_centroid_intersection'
            }

        # 3. String matching fallback
        district_name = district if district else 'Harare'
        normalized_name = district_name.strip().title()
        
        if normalized_name in self.district_spatial_index:
            data = self.district_spatial_index[normalized_name]
            lat_c, lon_c = data['center']
            return {
                'district': normalized_name,
                'province': data['province'],
                'agro_ecological_zone': data['agro_ecological_zone'],
                'soil_type': data['soil_type'],
                'soil_ph': data['soil_ph'],
                'altitude_m': data['altitude_m'],
                'latitude': lat_c,
                'longitude': lon_c,
                'lookup_method': 'district_string_fallback'
            }

        # Unknown location fallback
        default_data = self.district_spatial_index['Harare']
        return {
            'district': 'Harare',
            'province': default_data['province'],
            'agro_ecological_zone': default_data['agro_ecological_zone'],
            'soil_type': default_data['soil_type'],
            'soil_ph': default_data['soil_ph'],
            'altitude_m': default_data['altitude_m'],
            'latitude': default_data['center'][0],
            'longitude': default_data['center'][1],
            'lookup_method': 'district_string_fallback'
        }

    def _find_nearest_district(self, lat: float, lon: float) -> Tuple[str, float]:
        """Calculates approximate Haversine distance in kilometers to nearest district centroid"""
        min_dist = float('inf')
        nearest = 'Harare'

        for dist_name, data in self.district_spatial_index.items():
            c_lat, c_lon = data['center']
            d = self._haversine(lat, lon, c_lat, c_lon)
            if d < min_dist:
                min_dist = d
                nearest = dist_name

        return nearest, min_dist

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula for distance between 2 coordinates in kilometers"""
        R = 6371.0  # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


# Singleton spatial service instance
spatial_service = SpatialService()
