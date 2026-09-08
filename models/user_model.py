"""
User Model for AgricLedger Authentication
Handles user registration, login, 2FA, Land Records, and Data Access Requests
"""

import os
import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime
from flask_login import UserMixin
import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class User(UserMixin):
    """User class for authentication"""
    
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.first_name = user_data.get('first_name')
        self.last_name = user_data.get('last_name')
        self.email = user_data.get('email')
        self.phone = user_data.get('phone')
        self.location = user_data.get('location')
        self.farmer_id = user_data.get('farmer_id')
        self.password_hash = user_data.get('password_hash')
        self.two_factor_secret = user_data.get('two_factor_secret')
        self.two_factor_enabled = user_data.get('two_factor_enabled', False)
        self.created_at = user_data.get('created_at')
        self.last_login = user_data.get('last_login')
        self.role = user_data.get('role', 'farmer')
        self.bio = user_data.get('bio', '')  # Added bio field
        # Store active status in a private variable
        self._is_active = user_data.get('is_active', True)
    
    def get_id(self):
        return str(self.id)
    
    # Flask-Login required properties
    @property
    def is_active(self):
        """Return True if the user is active"""
        return self._is_active
    
    @property
    def is_authenticated(self):
        """Return True if the user is authenticated"""
        return True
    
    @property
    def is_anonymous(self):
        """Return True if the user is anonymous"""
        return False
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
    
    def enable_2fa(self):
        """Enable two-factor authentication"""
        self.two_factor_enabled = True
        self._save()
    
    def disable_2fa(self):
        """Disable two-factor authentication"""
        self.two_factor_enabled = False
        self._save()
    
    def get_2fa_qr_code(self):
        """Generate QR code for 2FA setup"""
        if not self.two_factor_secret:
            return None
        
        totp = pyotp.TOTP(self.two_factor_secret)
        uri = totp.provisioning_uri(self.email, issuer_name="AgricLedger")
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def verify_2fa(self, code):
        """Verify two-factor authentication code"""
        if not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(code)
    
    def _save(self):
        """Save user to database"""
        conn = get_db_connection()
        try:
            conn.execute('''
                UPDATE users SET
                    two_factor_enabled = ?,
                    last_login = ?
                WHERE id = ?
            ''', (self.two_factor_enabled, datetime.now().isoformat(), self.id))
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving user: {e}")
        finally:
            conn.close()


class UserManager:
    """Manager for user operations"""
    
    @staticmethod
    def create_user(first_name, last_name, email, phone, location, password, role='farmer'):
        """Create a new user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        existing = cursor.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            return {'success': False, 'error': 'Email already registered'}
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Get count for farmer ID
        count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        
        # Generate farmer ID
        farmer_id = f"F{datetime.now().strftime('%Y%m%d')}{count + 1:04d}"
        
        # Generate 2FA secret
        two_factor_secret = pyotp.random_base32()
        
        try:
            cursor.execute('''
                INSERT INTO users (
                    first_name, last_name, email, phone, location,
                    farmer_id, password_hash, two_factor_secret, role,
                    created_at, is_active, bio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                first_name, last_name, email, phone, location,
                farmer_id, password_hash, two_factor_secret, role,
                datetime.now().isoformat(), 1, ''
            ))
            conn.commit()
            
            user_id = cursor.lastrowid
            
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'farmer_id': farmer_id,
                'two_factor_secret': two_factor_secret
            }
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        cursor = conn.cursor()
        user_data = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user_data:
            return User(dict(user_data))
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        user_data = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user_data:
            return User(dict(user_data))
        return None
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        conn = get_db_connection()
        cursor = conn.cursor()
        users_data = cursor.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        conn.close()
        
        return [User(dict(user_data)) for user_data in users_data]
    
    @staticmethod
    def update_last_login(user_id):
        """Update last login timestamp"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                    (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def count_users():
        """Count total users"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def update_profile(user_id, data):
        """Update user profile"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET
                    first_name = ?,
                    last_name = ?,
                    phone = ?,
                    location = ?,
                    bio = ?
                WHERE id = ?
            ''', (
                data.get('first_name'),
                data.get('last_name'),
                data.get('phone'),
                data.get('location'),
                data.get('bio'),
                user_id
            ))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def change_password(user_id, new_password_hash):
        """Change user password"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE id = ?
            ''', (new_password_hash, user_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}


class LandRecord:
    """Model for land tenure records"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.owner_name = data.get('owner_name')
        self.national_id = data.get('national_id')
        self.phone = data.get('phone')
        self.email = data.get('email')
        self.deed_number = data.get('deed_number')
        self.farm_name = data.get('farm_name')
        self.plot_number = data.get('plot_number')
        self.size_hectares = data.get('size_hectares')
        self.district = data.get('district')
        self.province = data.get('province')
        self.gps_coordinates = data.get('gps_coordinates')
        self.town = data.get('town')
        self.tenure_type = data.get('tenure_type')
        self.use_rights = data.get('use_rights')
        self.transfer_rights = data.get('transfer_rights')
        self.acquisition_date = data.get('acquisition_date')
        self.boundaries = data.get('boundaries')
        self.encumbrances = data.get('encumbrances')
        self.document_url = data.get('document_url')
        self.status = data.get('status', 'Pending')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    @staticmethod
    def register_land(user_id, data):
        """Register a new land record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO land_records (
                    user_id, owner_name, national_id, phone, email, deed_number,
                    farm_name, plot_number, size_hectares, district, province,
                    gps_coordinates, town, tenure_type, use_rights, transfer_rights,
                    acquisition_date, boundaries, encumbrances, document_url, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data.get('owner_name'),
                data.get('national_id'),
                data.get('phone'),
                data.get('email'),
                data.get('deed_number'),
                data.get('farm_name'),
                data.get('plot_number'),
                float(data.get('size_hectares', 0)),
                data.get('district'),
                data.get('province'),
                data.get('gps_coordinates'),
                data.get('town'),
                data.get('tenure_type'),
                data.get('use_rights'),
                data.get('transfer_rights'),
                data.get('acquisition_date'),
                data.get('boundaries'),
                data.get('encumbrances'),
                data.get('document_url'),
                'Pending'
            ))
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f"Error registering land: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_land_records_by_user(user_id):
        """Get all land records for a specific user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        records = cursor.execute(
            'SELECT * FROM land_records WHERE user_id = ? ORDER BY created_at DESC', 
            (user_id,)
        ).fetchall()
        conn.close()
        return [LandRecord(dict(record)) for record in records]
    
    @staticmethod
    def get_all_land_records():
        """Get all land records (admin only)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        records = cursor.execute(
            'SELECT * FROM land_records ORDER BY created_at DESC'
        ).fetchall()
        conn.close()
        return [LandRecord(dict(record)) for record in records]
    
    @staticmethod
    def get_pending_land_records():
        """Get all pending land records"""
        conn = get_db_connection()
        cursor = conn.cursor()
        records = cursor.execute(
            'SELECT * FROM land_records WHERE status = "Pending" ORDER BY created_at DESC'
        ).fetchall()
        conn.close()
        return [LandRecord(dict(record)) for record in records]
    
    @staticmethod
    def approve_land(record_id):
        """Approve a land record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE land_records SET 
                    status = 'Approved',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (record_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error approving land: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reject_land(record_id):
        """Reject a land record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE land_records SET 
                    status = 'Rejected',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (record_id,))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error rejecting land: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def count_records():
        """Count total land records"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM land_records').fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def count_pending():
        """Count pending land records"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM land_records WHERE status = "Pending"').fetchone()[0]
        conn.close()
        return count


class DataAccessRecord:
    """Model for data access requests"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.farmer_id = data.get('farmer_id')
        self.organization = data.get('organization')
        self.purpose = data.get('purpose')
        self.data_type = data.get('data_type')
        self.status = data.get('status', 'Pending')
        self.requested_at = data.get('requested_at')
        self.responded_at = data.get('responded_at')
        self.access_count = data.get('access_count', 0)
        self.last_accessed_at = data.get('last_accessed_at')
    
    @staticmethod
    def create_request(farmer_id, organization, purpose, data_type):
        """Create a new data access request"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO data_access_requests (
                    farmer_id, organization, purpose, data_type, status, requested_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (farmer_id, organization, purpose, data_type, 'Pending', datetime.now().isoformat()))
            conn.commit()
            request_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'request_id': request_id}
        except Exception as e:
            logger.error(f"Error creating data access request: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def respond_to_request(request_id, status, farmer_id):
        """Respond to a data access request (grant/deny)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE data_access_requests SET 
                    status = ?,
                    responded_at = ?
                WHERE id = ? AND farmer_id = ?
            ''', (status, datetime.now().isoformat(), request_id, farmer_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error responding to request: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def log_access(request_id):
        """Log an access event"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE data_access_requests SET 
                    access_count = access_count + 1,
                    last_accessed_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_requests_by_farmer(farmer_id):
        """Get all requests for a specific farmer"""
        conn = get_db_connection()
        cursor = conn.cursor()
        requests = cursor.execute(
            'SELECT * FROM data_access_requests WHERE farmer_id = ? ORDER BY requested_at DESC',
            (farmer_id,)
        ).fetchall()
        conn.close()
        return [DataAccessRecord(dict(req)) for req in requests]
    
    @staticmethod
    def get_pending_requests_by_farmer(farmer_id):
        """Get pending requests for a specific farmer"""
        conn = get_db_connection()
        cursor = conn.cursor()
        requests = cursor.execute(
            'SELECT * FROM data_access_requests WHERE farmer_id = ? AND status = "Pending" ORDER BY requested_at DESC',
            (farmer_id,)
        ).fetchall()
        conn.close()
        return [DataAccessRecord(dict(req)) for req in requests]
    
    @staticmethod
    def get_all_requests():
        """Get all data access requests (admin only)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        requests = cursor.execute(
            'SELECT * FROM data_access_requests ORDER BY requested_at DESC'
        ).fetchall()
        conn.close()
        return [DataAccessRecord(dict(req)) for req in requests]
    
    @staticmethod
    def count_requests():
        """Count total data access requests"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM data_access_requests').fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def count_pending_requests():
        """Count pending data access requests"""
        conn = get_db_connection()
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM data_access_requests WHERE status = "Pending"').fetchone()[0]
        conn.close()
        return count


def get_db_connection():
    """Get database connection"""
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect('database/agricledger.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ========== USERS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            location TEXT,
            farmer_id TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            two_factor_secret TEXT,
            two_factor_enabled INTEGER DEFAULT 0,
            role TEXT DEFAULT 'farmer',
            created_at TEXT,
            last_login TEXT,
            is_active INTEGER DEFAULT 1,
            bio TEXT
        )
    ''')
    
    # ========== LAND RECORDS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            owner_name TEXT NOT NULL,
            national_id TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            deed_number TEXT UNIQUE NOT NULL,
            farm_name TEXT NOT NULL,
            plot_number TEXT NOT NULL,
            size_hectares REAL NOT NULL,
            district TEXT NOT NULL,
            province TEXT NOT NULL,
            gps_coordinates TEXT,
            town TEXT NOT NULL,
            tenure_type TEXT NOT NULL,
            use_rights TEXT NOT NULL,
            transfer_rights TEXT NOT NULL,
            acquisition_date TEXT NOT NULL,
            boundaries TEXT,
            encumbrances TEXT,
            document_url TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ========== CROP RECORDS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crop_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            crop_type TEXT NOT NULL,
            variety TEXT,
            planting_date TEXT NOT NULL,
            harvest_date TEXT,
            land_size REAL NOT NULL,
            yield_tonnes REAL NOT NULL,
            fertilizer TEXT,
            watering_method TEXT,
            pest_control TEXT,
            notes TEXT,
            success_rate INTEGER DEFAULT 75,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ========== DATA ACCESS REQUESTS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_access_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            organization TEXT NOT NULL,
            purpose TEXT,
            data_type TEXT,
            status TEXT DEFAULT 'Pending',
            requested_at TEXT,
            responded_at TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed_at TEXT,
            FOREIGN KEY (farmer_id) REFERENCES users (id)
        )
    ''')
    
    # ========== SESSIONS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # ========== REVIEWS TABLE ==========
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            recommend TEXT NOT NULL,
            features TEXT,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # =============================================================
    # ========== MARKET TABLES - OBJECTIVE 5 ==========
    # =============================================================
    
    # 1. Crops in demand table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            demand_score INTEGER DEFAULT 0,
            trend TEXT DEFAULT 'stable',
            icon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Buyers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_buyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            crops_bought TEXT,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Price ranges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            location TEXT NOT NULL,
            price_min REAL NOT NULL,
            price_max REAL NOT NULL,
            unit TEXT DEFAULT 'tonne',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Suppliers/Input Providers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            products TEXT,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            is_active INTEGER DEFAULT 1,
            rating REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Financial Institutes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_financial_institutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            loan_types TEXT,
            interest_rate REAL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 6. Market Demand Trends (for charts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            location TEXT NOT NULL,
            month TEXT NOT NULL,
            demand_tonnes REAL,
            supply_tonnes REAL,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 7. Market Activity Feed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized with all tables including bio field and market tables")
    
    # ========== SEED INITIAL MARKET DATA ==========
    seed_market_data()


def seed_market_data():
    """Seed initial market data for Objective 5"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if data already exists
    count = cursor.execute('SELECT COUNT(*) FROM market_crops').fetchone()[0]
    if count > 0:
        logger.info("Market data already seeded, skipping...")
        conn.close()
        return
    
    logger.info("🌾 Seeding market data...")
    
    try:
        # ===== SEED CROPS IN DEMAND =====
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
        logger.info("  ✅ Crops seeded")
        
        # ===== SEED BUYERS =====
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
        logger.info("  ✅ Buyers seeded")
        
        # ===== SEED PRICES =====
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
        logger.info("  ✅ Prices seeded")
        
        # ===== SEED SUPPLIERS =====
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
        logger.info("  ✅ Suppliers seeded")
        
        # ===== SEED FINANCIAL INSTITUTES =====
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
        logger.info("  ✅ Financial Institutes seeded")
        
        # ===== SEED MARKET TRENDS =====
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
        logger.info("  ✅ Market Trends seeded")
        
        # ===== SEED MARKET ACTIVITY =====
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
        logger.info("  ✅ Market Activity seeded")
        
        conn.commit()
        conn.close()
        logger.info("✅ Market data seeded successfully for Objective 5!")
        
    except Exception as e:
        logger.error(f"Error seeding market data: {e}")
        conn.close()