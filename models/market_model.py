"""
Market Model for AgricLedger
Handles market data, buyers, suppliers, financial institutes, and price tracking
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from models.user_model import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketCrop:
    """Model for crops in demand"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.crop_name = data.get('crop_name')
        self.demand_score = data.get('demand_score', 0)
        self.trend = data.get('trend', 'stable')
        self.icon = data.get('icon')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all crops in demand"""
        conn = get_db_connection()
        crops = conn.execute(
            'SELECT * FROM market_crops ORDER BY demand_score DESC'
        ).fetchall()
        conn.close()
        return [dict(c) for c in crops]
    
    @staticmethod
    def get_top_demand(limit: int = 5) -> List[Dict]:
        """Get top N crops in demand"""
        conn = get_db_connection()
        crops = conn.execute(
            'SELECT * FROM market_crops ORDER BY demand_score DESC LIMIT ?',
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(c) for c in crops]
    
    @staticmethod
    def update_demand(crop_name: str, demand_score: int):
        """Update demand score for a crop"""
        conn = get_db_connection()
        conn.execute('''
            UPDATE market_crops 
            SET demand_score = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE crop_name = ?
        ''', (demand_score, crop_name))
        conn.commit()
        conn.close()


class MarketBuyer:
    """Model for market buyers"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.location = data.get('location')
        self.crops_bought = json.loads(data.get('crops_bought', '[]')) if isinstance(data.get('crops_bought'), str) else data.get('crops_bought', [])
        self.contact_person = data.get('contact_person')
        self.phone = data.get('phone')
        self.email = data.get('email')
        self.is_active = data.get('is_active', 1)
        self.created_at = data.get('created_at')
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all buyers"""
        conn = get_db_connection()
        if active_only:
            buyers = conn.execute(
                'SELECT * FROM market_buyers WHERE is_active = 1 ORDER BY name'
            ).fetchall()
        else:
            buyers = conn.execute('SELECT * FROM market_buyers ORDER BY name').fetchall()
        conn.close()
        return [dict(b) for b in buyers]
    
    @staticmethod
    def get_by_location(location: str) -> List[Dict]:
        """Get buyers by location"""
        conn = get_db_connection()
        buyers = conn.execute(
            'SELECT * FROM market_buyers WHERE location = ? AND is_active = 1 ORDER BY name',
            (location,)
        ).fetchall()
        conn.close()
        return [dict(b) for b in buyers]
    
    @staticmethod
    def get_by_crop(crop: str) -> List[Dict]:
        """Get buyers by crop they purchase"""
        conn = get_db_connection()
        # Search for crop in JSON string
        buyers = conn.execute('''
            SELECT * FROM market_buyers 
            WHERE is_active = 1 AND crops_bought LIKE ?
            ORDER BY name
        ''', (f'%{crop}%',)).fetchall()
        conn.close()
        return [dict(b) for b in buyers]
    
    @staticmethod
    def add_buyer(data: Dict) -> Dict:
        """Add a new buyer"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            crops_json = json.dumps(data.get('crops_bought', []))
            cursor.execute('''
                INSERT INTO market_buyers (
                    name, location, crops_bought, contact_person, phone, email, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('location'),
                crops_json,
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                1
            ))
            conn.commit()
            buyer_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            MarketActivity.add_activity(
                'buyer_added',
                f'New buyer registered: {data.get("name")}',
                f'{data.get("name")} is now buying crops in {data.get("location")}'
            )
            
            return {'success': True, 'id': buyer_id}
        except Exception as e:
            logger.error(f"Error adding buyer: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class MarketPrice:
    """Model for market prices"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.crop_name = data.get('crop_name')
        self.location = data.get('location')
        self.price_min = data.get('price_min')
        self.price_max = data.get('price_max')
        self.unit = data.get('unit', 'tonne')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all prices"""
        conn = get_db_connection()
        prices = conn.execute(
            'SELECT * FROM market_prices ORDER BY crop_name, location'
        ).fetchall()
        conn.close()
        return [dict(p) for p in prices]
    
    @staticmethod
    def get_by_crop(crop_name: str) -> List[Dict]:
        """Get prices for a specific crop"""
        conn = get_db_connection()
        prices = conn.execute(
            'SELECT * FROM market_prices WHERE crop_name = ? ORDER BY location',
            (crop_name,)
        ).fetchall()
        conn.close()
        return [dict(p) for p in prices]
    
    @staticmethod
    def get_by_location(location: str) -> List[Dict]:
        """Get prices for a specific location"""
        conn = get_db_connection()
        prices = conn.execute(
            'SELECT * FROM market_prices WHERE location = ? ORDER BY crop_name',
            (location,)
        ).fetchall()
        conn.close()
        return [dict(p) for p in prices]
    
    @staticmethod
    def update_price(data: Dict) -> Dict:
        """Add or update a price"""
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO market_prices (crop_name, location, price_min, price_max, unit)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT DO UPDATE SET
                    price_min = excluded.price_min,
                    price_max = excluded.price_max,
                    unit = excluded.unit,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                data.get('crop_name'),
                data.get('location'),
                data.get('price_min'),
                data.get('price_max'),
                data.get('unit', 'tonne')
            ))
            conn.commit()
            conn.close()
            
            # Log activity
            MarketActivity.add_activity(
                'price_update',
                f'Price update: {data.get("crop_name")} in {data.get("location")}',
                f'Range: ${data.get("price_min")} - ${data.get("price_max")} per {data.get("unit", "tonne")}'
            )
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Error updating price: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class MarketSupplier:
    """Model for input suppliers"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.category = data.get('category')
        self.location = data.get('location')
        self.products = json.loads(data.get('products', '[]')) if isinstance(data.get('products'), str) else data.get('products', [])
        self.contact_person = data.get('contact_person')
        self.phone = data.get('phone')
        self.email = data.get('email')
        self.website = data.get('website')
        self.is_active = data.get('is_active', 1)
        self.rating = data.get('rating', 0)
        self.created_at = data.get('created_at')
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all suppliers"""
        conn = get_db_connection()
        if active_only:
            suppliers = conn.execute(
                'SELECT * FROM market_suppliers WHERE is_active = 1 ORDER BY rating DESC, name'
            ).fetchall()
        else:
            suppliers = conn.execute('SELECT * FROM market_suppliers ORDER BY name').fetchall()
        conn.close()
        return [dict(s) for s in suppliers]
    
    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """Get suppliers by category"""
        conn = get_db_connection()
        suppliers = conn.execute(
            'SELECT * FROM market_suppliers WHERE category = ? AND is_active = 1 ORDER BY rating DESC',
            (category,)
        ).fetchall()
        conn.close()
        return [dict(s) for s in suppliers]
    
    @staticmethod
    def get_by_location(location: str) -> List[Dict]:
        """Get suppliers by location"""
        conn = get_db_connection()
        suppliers = conn.execute(
            'SELECT * FROM market_suppliers WHERE location = ? AND is_active = 1 ORDER BY name',
            (location,)
        ).fetchall()
        conn.close()
        return [dict(s) for s in suppliers]
    
    @staticmethod
    def add_supplier(data: Dict) -> Dict:
        """Add a new supplier"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            products_json = json.dumps(data.get('products', []))
            cursor.execute('''
                INSERT INTO market_suppliers (
                    name, category, location, products, contact_person, phone, email, website, rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('category'),
                data.get('location'),
                products_json,
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                data.get('website'),
                float(data.get('rating', 0))
            ))
            conn.commit()
            supplier_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            MarketActivity.add_activity(
                'new_supplier',
                f'New supplier: {data.get("name")}',
                f'{data.get("name")} provides {data.get("category")} in {data.get("location")}'
            )
            
            return {'success': True, 'id': supplier_id}
        except Exception as e:
            logger.error(f"Error adding supplier: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class FinancialInstitute:
    """Model for financial institutes"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.location = data.get('location')
        self.loan_types = json.loads(data.get('loan_types', '[]')) if isinstance(data.get('loan_types'), str) else data.get('loan_types', [])
        self.interest_rate = data.get('interest_rate')
        self.contact_person = data.get('contact_person')
        self.phone = data.get('phone')
        self.email = data.get('email')
        self.website = data.get('website')
        self.is_active = data.get('is_active', 1)
        self.created_at = data.get('created_at')
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all financial institutes"""
        conn = get_db_connection()
        if active_only:
            institutes = conn.execute(
                'SELECT * FROM market_financial_institutes WHERE is_active = 1 ORDER BY name'
            ).fetchall()
        else:
            institutes = conn.execute('SELECT * FROM market_financial_institutes ORDER BY name').fetchall()
        conn.close()
        return [dict(i) for i in institutes]
    
    @staticmethod
    def get_by_type(type_name: str) -> List[Dict]:
        """Get institutes by type"""
        conn = get_db_connection()
        institutes = conn.execute(
            'SELECT * FROM market_financial_institutes WHERE type = ? AND is_active = 1 ORDER BY name',
            (type_name,)
        ).fetchall()
        conn.close()
        return [dict(i) for i in institutes]
    
    @staticmethod
    def get_by_location(location: str) -> List[Dict]:
        """Get institutes by location"""
        conn = get_db_connection()
        institutes = conn.execute(
            'SELECT * FROM market_financial_institutes WHERE location = ? AND is_active = 1 ORDER BY name',
            (location,)
        ).fetchall()
        conn.close()
        return [dict(i) for i in institutes]
    
    @staticmethod
    def add_institute(data: Dict) -> Dict:
        """Add a new financial institute"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            loans_json = json.dumps(data.get('loan_types', []))
            cursor.execute('''
                INSERT INTO market_financial_institutes (
                    name, type, location, loan_types, interest_rate, contact_person, phone, email, website
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('type'),
                data.get('location'),
                loans_json,
                float(data.get('interest_rate', 0)),
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                data.get('website')
            ))
            conn.commit()
            institute_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            MarketActivity.add_activity(
                'new_loan',
                f'New financial institute: {data.get("name")}',
                f'{data.get("name")} offers loans in {data.get("location")}'
            )
            
            return {'success': True, 'id': institute_id}
        except Exception as e:
            logger.error(f"Error adding institute: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class MarketTrend:
    """Model for market demand trends"""
    
    @staticmethod
    def get_trends(crop_name: str = None, location: str = None, months: int = 12) -> List[Dict]:
        """Get market trends for charts"""
        conn = get_db_connection()
        
        query = '''
            SELECT crop_name, location, month, demand_tonnes, supply_tonnes, year
            FROM market_trends
            WHERE 1=1
        '''
        params = []
        
        if crop_name:
            query += ' AND crop_name = ?'
            params.append(crop_name)
        if location:
            query += ' AND location = ?'
            params.append(location)
        
        query += ' ORDER BY year DESC, month DESC LIMIT ?'
        params.append(months)
        
        trends = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(t) for t in trends]
    
    @staticmethod
    def add_trend(data: Dict) -> Dict:
        """Add a trend data point"""
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO market_trends (crop_name, location, month, demand_tonnes, supply_tonnes, year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data.get('crop_name'),
                data.get('location'),
                data.get('month'),
                float(data.get('demand_tonnes', 0)),
                float(data.get('supply_tonnes', 0)),
                int(data.get('year', datetime.now().year))
            ))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error adding trend: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class MarketActivity:
    """Model for market activity feed"""
    
    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict]:
        """Get recent market activities"""
        conn = get_db_connection()
        activities = conn.execute(
            'SELECT * FROM market_activity ORDER BY created_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(a) for a in activities]
    
    @staticmethod
    def add_activity(activity_type: str, title: str, description: str = None, icon: str = None):
        """Add a market activity"""
        conn = get_db_connection()
        try:
            icons = {
                'buyer_added': '🏢',
                'price_update': '💰',
                'new_supplier': '📦',
                'new_loan': '🏦',
                'market_alert': '📢'
            }
            if not icon:
                icon = icons.get(activity_type, '📊')
            
            conn.execute('''
                INSERT INTO market_activity (type, title, description, icon)
                VALUES (?, ?, ?, ?)
            ''', (activity_type, title, description, icon))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding activity: {e}")
            conn.close()


# ========== INITIAL SEED DATA ==========

def seed_market_data():
    """Seed initial market data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if data exists
    count = cursor.execute('SELECT COUNT(*) FROM market_crops').fetchone()[0]
    if count > 0:
        logger.info("Market data already seeded")
        conn.close()
        return
    
    # Seed crops in demand
    crops = [
        ('Maize', 92, 'up', '🌽'),
        ('Tobacco', 85, 'up', '🚬'),
        ('Soybean', 78, 'stable', '🌱'),
        ('Wheat', 70, 'down', '🌾'),
        ('Sorghum', 65, 'up', '🌿'),
        ('Cotton', 60, 'stable', '🧶'),
        ('Groundnuts', 55, 'up', '🥜'),
        ('Sunflower', 50, 'down', '🌻'),
        ('SweetPotato', 45, 'stable', '🍠'),
        ('Cassava', 40, 'down', '🍠')
    ]
    for crop in crops:
        cursor.execute('''
            INSERT INTO market_crops (crop_name, demand_score, trend, icon)
            VALUES (?, ?, ?, ?)
        ''', crop)
    
    # Seed buyers
    buyers = [
        ('Grain Marketing Board (GMB)', 'Harare', '["Maize", "Wheat", "Sorghum"]', 'Mr. Chikwanda', '+263772123456', 'info@gmb.co.zw'),
        ('Zimbabwe Tobacco Association', 'Harare', '["Tobacco"]', 'Mrs. Moyo', '+263772123457', 'tobacco@zta.co.zw'),
        ('National Foods', 'Bulawayo', '["Maize", "Wheat", "Soybean"]', 'Mr. Ndlovu', '+263772123458', 'procurement@natfoods.co.zw'),
        ('Cargill Zimbabwe', 'Mutare', '["Cotton", "Soybean"]', 'Ms. Dube', '+263772123459', 'info@cargill.co.zw'),
        ('AFGRI Zimbabwe', 'Gweru', '["Maize", "Sorghum", "Sunflower"]', 'Mr. Sibanda', '+263772123460', 'info@afgri.co.zw'),
        ('Zimbabwe Agro-Processing', 'Masvingo', '["Groundnuts", "SweetPotato", "Cassava"]', 'Mrs. Chirwa', '+263772123461', 'info@zap.co.zw'),
        ('Local Market Traders', 'Harare', '["Maize", "Vegetables", "Groundnuts"]', 'Mr. Mupfumira', '+263772123462', 'traders@local.co.zw'),
    ]
    for buyer in buyers:
        cursor.execute('''
            INSERT INTO market_buyers (name, location, crops_bought, contact_person, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', buyer)
    
    # Seed prices
    prices = [
        ('Maize', 'Harare', 350, 420, 'tonne'),
        ('Maize', 'Bulawayo', 330, 400, 'tonne'),
        ('Maize', 'Mutare', 340, 410, 'tonne'),
        ('Tobacco', 'Harare', 2800, 3200, 'tonne'),
        ('Tobacco', 'Bulawayo', 2700, 3100, 'tonne'),
        ('Soybean', 'Harare', 600, 750, 'tonne'),
        ('Soybean', 'Bulawayo', 580, 720, 'tonne'),
        ('Wheat', 'Harare', 450, 520, 'tonne'),
        ('Wheat', 'Gweru', 430, 500, 'tonne'),
        ('Sorghum', 'Harare', 280, 350, 'tonne'),
        ('Sorghum', 'Bulawayo', 260, 330, 'tonne'),
        ('Cotton', 'Harare', 850, 950, 'tonne'),
        ('Cotton', 'Mutare', 820, 920, 'tonne'),
        ('Groundnuts', 'Harare', 500, 600, 'tonne'),
        ('Groundnuts', 'Masvingo', 480, 580, 'tonne'),
        ('Sunflower', 'Harare', 400, 480, 'tonne'),
        ('Sunflower', 'Gweru', 380, 460, 'tonne'),
        ('SweetPotato', 'Harare', 200, 300, 'tonne'),
        ('Cassava', 'Harare', 180, 250, 'tonne'),
    ]
    for price in prices:
        cursor.execute('''
            INSERT INTO market_prices (crop_name, location, price_min, price_max, unit)
            VALUES (?, ?, ?, ?, ?)
        ''', price)
    
    # Seed suppliers
    suppliers = [
        ('SeedCo Zimbabwe', 'Seed', 'Harare', '["Maize", "Wheat", "Soybean", "Sorghum"]', 'Mr. Madzima', '+263772123470', 'info@seedco.co.zw', 'www.seedco.co.zw', 4.5),
        ('ZFC Fertilizer', 'Fertilizer', 'Bulawayo', '["Compound D", "Urea", "Ammonium Nitrate", "NPK"]', 'Mrs. Makoni', '+263772123471', 'info@zfc.co.zw', 'www.zfc.co.zw', 4.2),
        ('John Deere Zimbabwe', 'Equipment', 'Harare', '["Tractors", "Ploughs", "Harvesters", "Irrigation"]', 'Mr. Smith', '+263772123472', 'info@johndeere.co.zw', 'www.johndeere.co.zw', 4.8),
        ('AgriSeeds', 'Seed', 'Harare', '["Tobacco", "Cotton", "Groundnuts", "Sunflower"]', 'Ms. Muchena', '+263772123473', 'info@agriseeds.co.zw', 'www.agriseeds.co.zw', 4.0),
        ('Zim Pesticides', 'Pesticide', 'Harare', '["Insecticides", "Fungicides", "Herbicides"]', 'Mr. Gumbo', '+263772123474', 'info@zimpesticides.co.zw', 'www.zimpesticides.co.zw', 3.8),
        ('Farm Equipment', 'Equipment', 'Bulawayo', '["Irrigation Systems", "Sprayers", "Planters", "Tillers"]', 'Mrs. Ncube', '+263772123475', 'info@famequip.co.zw', 'www.famequip.co.zw', 4.3),
        ('AgriFeed Zimbabwe', 'Feed', 'Harare', '["Animal Feed", "Poultry Feed", "Livestock Feed"]', 'Mr. Chikomo', '+263772123476', 'info@agrifeed.co.zw', 'www.agrifeed.co.zw', 4.0),
    ]
    for supplier in suppliers:
        cursor.execute('''
            INSERT INTO market_suppliers (name, category, location, products, contact_person, phone, email, website, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', supplier)
    
    # Seed financial institutes
    institutes = [
        ('CBZ Bank', 'Bank', 'Harare', '["Agricultural Loans", "Equipment Finance", "Working Capital"]', 12.5, 'Mrs. Mangwende', '+263772123480', 'info@cbz.co.zw', 'www.cbz.co.zw'),
        ('Agribank', 'Bank', 'Harare', '["Farm Loans", "Input Finance", "Land Purchase"]', 10.0, 'Mr. Makore', '+263772123481', 'info@agribank.co.zw', 'www.agribank.co.zw'),
        ('NMB Bank', 'Bank', 'Bulawayo', '["Agricultural Loans", "Export Finance", "Working Capital"]', 13.0, 'Ms. Sibanda', '+263772123482', 'info@nmb.co.zw', 'www.nmb.co.zw'),
        ('Microfinance Zimbabwe', 'Microfinance', 'Harare', '["Small Farm Loans", "Input Loans", "Livestock Loans"]', 18.0, 'Mr. Moyo', '+263772123483', 'info@mfz.co.zw', 'www.mfz.co.zw'),
        ('FBC Bank', 'Bank', 'Harare', '["Agri Loans", "Asset Finance", "Trade Finance"]', 11.5, 'Mrs. Dube', '+263772123484', 'info@fbc.co.zw', 'www.fbc.co.zw'),
        ('Zimbabwe Farmers Union', 'Cooperative', 'Harare', '["Group Loans", "Input Schemes", "Insurance"]', 8.0, 'Mr. Ndlovu', '+263772123485', 'info@zfu.co.zw', 'www.zfu.co.zw'),
        ('Old Mutual', 'Insurance', 'Harare', '["Crop Insurance", "Livestock Insurance", "Farm Insurance"]', None, 'Ms. Chirwa', '+263772123486', 'info@oldmutual.co.zw', 'www.oldmutual.co.zw'),
    ]
    for institute in institutes:
        cursor.execute('''
            INSERT INTO market_financial_institutes (name, type, location, loan_types, interest_rate, contact_person, phone, email, website)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', institute)
    
    # Seed market trends
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    crops_trends = ['Maize', 'Tobacco', 'Soybean', 'Wheat', 'Sorghum']
    
    for crop in crops_trends:
        for i, month in enumerate(months):
            demand = 100 + i * 15 + (i % 5) * 10
            supply = 80 + i * 10 + (i % 3) * 5
            cursor.execute('''
                INSERT INTO market_trends (crop_name, location, month, demand_tonnes, supply_tonnes, year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (crop, 'Harare', month, demand, supply, 2024))
    
    # Seed market activity
    activities = [
        ('buyer_added', 'New buyer registered: Grain Marketing Board', 'GMB is now buying maize and wheat in bulk', '🏢'),
        ('price_update', 'Maize prices increased in Harare', 'Maize now trading at $350-420 per tonne', '💰'),
        ('new_supplier', 'New supplier: SeedCo Zimbabwe', 'SeedCo offers quality maize and wheat seeds', '📦'),
        ('new_loan', 'Agribank launches new farm loan product', 'Low interest loans for input financing', '🏦'),
        ('market_alert', 'High demand for tobacco in Bulawayo', 'Tobacco prices expected to rise', '📢'),
        ('buyer_added', 'Cargill Zimbabwe joins the platform', 'Cargill now buying cotton and soybean', '🏢'),
        ('price_update', 'Soybean prices stable at $600-750 per tonne', 'Good time to sell soybean', '💰'),
        ('new_supplier', 'John Deere expands in Zimbabwe', 'Quality farm equipment now available', '📦'),
    ]
    for activity in activities:
        cursor.execute('''
            INSERT INTO market_activity (type, title, description, icon)
            VALUES (?, ?, ?, ?)
        ''', activity)
    
    conn.commit()
    conn.close()
    logger.info("✅ Market data seeded successfully")