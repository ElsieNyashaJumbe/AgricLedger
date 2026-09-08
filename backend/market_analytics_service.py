"""
Market Analytics Service for AgricLedger
Processes 7-day market datasets for Harare, Bulawayo, and Mutare.
Computes price ranges, averages, 7-day price changes, demand/supply levels, and supply gaps.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'market_7day_data.csv')


class MarketAnalyticsService:
    """
    Service for calculating 7-day rolling market statistics, supply gaps, and price trends.
    """
    
    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load market dataset F"""
        if os.path.exists(self.data_path):
            try:
                self.df = pd.read_csv(self.data_path)
                self.df['date'] = pd.to_datetime(self.df['date'])
                logger.info(f"[OK] Market analytics loaded {len(self.df)} records from {self.data_path}")
            except Exception as e:
                logger.error(f"Error loading market data: {e}")
                self.df = None
        else:
            logger.warning(f"Market dataset not found at {self.data_path}")
            self.df = None
            
    def get_latest_7day_analytics(self, market: str = None, crop: str = None) -> dict:
        """
        Filters the most recent 7 days of observed market data and calculates:
        - minimum_price, maximum_price, average_price
        - price_change_7d (%)
        - demand_level, supply_level
        - supply_gap (demand - supply)
        """
        if self.df is None or len(self.df) == 0:
            self.load_data()
            if self.df is None:
                return {'success': False, 'error': 'Market dataset unavailable'}
                
        filtered_df = self.df.copy()
        
        if market:
            filtered_df = filtered_df[filtered_df['market'].str.lower() == market.lower()]
        if crop:
            filtered_df = filtered_df[filtered_df['crop'].str.lower() == crop.lower()]
            
        if len(filtered_df) == 0:
            return {'success': False, 'error': f'No data found for market={market}, crop={crop}'}
            
        # Get latest 7 dates
        latest_date = filtered_df['date'].max()
        cutoff_date = latest_date - pd.Timedelta(days=6)
        
        last_7_days_df = filtered_df[filtered_df['date'] >= cutoff_date]
        
        # Group by Market and Crop
        analytics_list = []
        
        grouped = last_7_days_df.groupby(['market', 'crop'])
        
        for (mkt, crp), group in grouped:
            sorted_g = group.sort_values('date')
            
            p_min = round(float(sorted_g['minimum_price'].min()), 2)
            p_max = round(float(sorted_g['maximum_price'].max()), 2)
            p_avg = round(float(sorted_g['average_price'].mean()), 2)
            
            # Price change over 7 days
            p_start = float(sorted_g['average_price'].iloc[0])
            p_end = float(sorted_g['average_price'].iloc[-1])
            price_change = round(((p_end - p_start) / p_start) * 100.0, 2) if p_start > 0 else 0.0
            
            demand_avg = round(float(sorted_g['demand_level'].mean()), 1)
            supply_avg = round(float(sorted_g['supply_level'].mean()), 1)
            supply_gap = round(demand_avg - supply_avg, 1) # Positive = deficit/shortage, Negative = surplus
            
            trend_str = 'UPWARD' if price_change > 1.0 else ('DOWNWARD' if price_change < -1.0 else 'STABLE')
            
            analytics_list.append({
                'market': mkt,
                'crop': crp,
                'observation_period': f"{cutoff_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}",
                'days_count': len(sorted_g['date'].unique()),
                'minimum_price': p_min,
                'maximum_price': p_max,
                'average_price': p_avg,
                'price_change_7d_pct': price_change,
                'price_trend': trend_str,
                'demand_level_tonnes': demand_avg,
                'supply_level_tonnes': supply_avg,
                'supply_gap_tonnes': supply_gap,
                'market_status': 'SHORTAGE / HIGH DEMAND' if supply_gap > 0 else 'SURPLUS / ADEQUATE',
                'data_classification': 'SYNTHETIC MARKET DATA (DEVELOPMENT BASELINE)',
                'is_synthetic': True
            })
            
        return {
            'success': True,
            'latest_date': latest_date.strftime('%Y-%m-%d'),
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'total_analytics_records': len(analytics_list),
            'analytics': analytics_list
        }


# Singleton market analytics service
market_analytics_service = MarketAnalyticsService()
