"""
AgricLedger - Main Application Entry Point
A blockchain-based digital ecosystem for farmer data sovereignty,
land title management, and agricultural value chain integration in Zimbabwe.
"""

import os
import json
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Authentication imports
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.user_model import User, UserManager, init_db
from forms.auth_forms import RegistrationForm, LoginForm, TwoFactorForm
import pyotp
import qrcode

# Import blockchain connector
from blockchain.interaction.blockchain_connector import BlockchainConnector

# Import weather and crop modules
from backend.weather_service import weather_service
from models.crop_suitability_model import crop_model

# Import chatbot module
from backend.chatbot_service import chatbot

# Import market analytics module
try:
    from backend.market_analytics_service import market_analytics_service
except ImportError:
    market_analytics_service = None
    logger = logging.getLogger(__name__)
    logger.warning("Market analytics service not found. Some features may be limited.")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return UserManager.get_user_by_id(int(user_id))

# Initialize database
init_db()

# Enable CORS for API access
CORS(app)

# Initialize blockchain connector
blockchain = BlockchainConnector()


# ============================================================
# HELPER FUNCTION: ADMIN CHECK
# ============================================================

def is_admin_user():
    """Check if the current user is an admin based on role"""
    return current_user.is_authenticated and current_user.role == 'admin'


# ============================================================
# HOME, DASHBOARD & HEALTH ROUTES
# ============================================================

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the farmer dashboard"""
    return render_template('dashboard.html', user=current_user)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'project': 'AgricLedger',
        'version': '1.0.0',
        'blockchain': {
            'connected': blockchain.w3.is_connected() if blockchain.w3 else False,
            'network': blockchain.network
        }
    })


# ============================================================
# USER ROLE API
# ============================================================

@app.route('/api/user/role')
@login_required
def get_user_role():
    """Get current user's role"""
    return jsonify({
        'success': True,
        'role': current_user.role,
        'is_admin': current_user.role == 'admin'
    })


# ============================================================
# WEATHER ROUTES
# ============================================================

@app.route('/api/weather/test')
def test_weather_api():
    """Test the weather API connection"""
    result = weather_service.test_api_connection()
    return jsonify(result)

@app.route('/api/weather/current/<location>')
@login_required
def get_current_weather(location):
    """Get current weather for a location"""
    try:
        logger.info(f"Fetching current weather for: {location}")
        result = weather_service.get_current_weather(location)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_current_weather: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather/forecast/<location>')
@login_required
def get_weather_forecast(location):
    """Get 7-day weather forecast for a location"""
    try:
        logger.info(f"Fetching 7-day forecast for: {location}")
        result = weather_service.get_7_day_forecast(location)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_weather_forecast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = UserManager.get_user_by_email(form.email.data)
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user - role is passed from the form
        result = UserManager.create_user(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
            phone=form.phone.data,
            location=form.location.data,
            role=form.role.data
        )
        
        if result.get('success'):
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {result.get("error", "Please try again.")}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = UserManager.get_user_by_email(form.email.data)
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('login.html', form=form)
            
            # Store user ID in session for 2FA check
            session['login_user_id'] = user.id
            session['remember_me'] = form.remember_me.data
            
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                return redirect(url_for('verify_2fa'))
            else:
                # Login without 2FA
                login_user(user, remember=form.remember_me.data)
                UserManager.update_last_login(user.id)
                flash(f'Welcome back, {user.first_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Two-factor authentication verification"""
    if 'login_user_id' not in session:
        return redirect(url_for('login'))
    
    user = UserManager.get_user_by_id(session['login_user_id'])
    if not user:
        session.pop('login_user_id', None)
        return redirect(url_for('login'))
    
    form = TwoFactorForm()
    
    if form.validate_on_submit():
        if user.verify_2fa(form.code.data):
            # Login successful
            login_user(user, remember=session.get('remember_me', False))
            UserManager.update_last_login(user.id)
            session.pop('login_user_id', None)
            session.pop('remember_me', None)
            flash(f'Welcome back, {user.first_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid authentication code. Please try again.', 'danger')
    
    return render_template('verify_2fa.html', form=form, user=user)

@app.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup two-factor authentication"""
    user = current_user
    
    if user.two_factor_enabled:
        flash('2FA is already enabled for your account.', 'info')
        return redirect(url_for('dashboard'))
    
    # Get 2FA secret from session or generate new
    if '2fa_secret' not in session:
        session['2fa_secret'] = pyotp.random_base32()
    
    secret = session['2fa_secret']
    totp = pyotp.TOTP(secret)
    
    # Generate QR code
    uri = totp.provisioning_uri(user.email, issuer_name="AgricLedger")
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    form = TwoFactorForm()
    
    if form.validate_on_submit():
        if totp.verify(form.code.data):
            # Enable 2FA for user
            user.two_factor_secret = secret
            user.enable_2fa()
            session.pop('2fa_secret', None)
            session.pop('2fa_setup_required', None)
            flash('✅ Two-Factor Authentication enabled successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid authentication code. Please try again.', 'danger')
    
    return render_template('setup_2fa.html', 
                          form=form, 
                          user=user, 
                          qr_code=f"data:image/png;base64,{qr_base64}",
                          secret=secret)

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)


# ============================================================
# BLOCKCHAIN ROUTES
# ============================================================

@app.route('/api/blockchain/register-farmer', methods=['POST'])
@login_required
def register_farmer():
    """Register a farmer on the blockchain"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        farmer_id = data.get('farmer_id')
        name = data.get('name')
        location = data.get('location')
        
        if not farmer_id or not name or not location:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        result = blockchain.register_farmer(farmer_id, name, location)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in register_farmer endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/grant-access', methods=['POST'])
@login_required
def grant_access():
    """Grant data access to an organization"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        org_address = data.get('organization_address')
        data_type = data.get('data_type')
        purpose = data.get('purpose')
        
        if not org_address or not data_type or not purpose:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        result = blockchain.grant_data_access(org_address, data_type, purpose)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in grant_access endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/revoke-access', methods=['POST'])
@login_required
def revoke_access():
    """Revoke data access from an organization"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        org_address = data.get('organization_address')
        
        if not org_address:
            return jsonify({'success': False, 'error': 'Organization address required'}), 400
        
        result = blockchain.revoke_data_access(org_address)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in revoke_access endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/register-land', methods=['POST'])
@login_required
def register_land():
    """Register land tenure record on blockchain"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        result = blockchain.register_land(
            land_id=data.get('land_id'),
            location=data.get('location'),
            document_type=data.get('document_type'),
            document_hash=data.get('document_hash'),
            plot_number=data.get('plot_number'),
            district=data.get('district'),
            province=data.get('province'),
            size_hectares=float(data.get('size_hectares', 0))
        )
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in register_land endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/land/<land_id>')
@login_required
def get_land(land_id):
    """Get land record from blockchain"""
    try:
        result = blockchain.get_land_record(land_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_land endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/access-history/<farmer_address>')
@login_required
def get_access_history(farmer_address):
    """Get access history for a farmer"""
    try:
        result = blockchain.get_access_history(farmer_address)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_access_history endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/check-access/<farmer>/<org>')
@login_required
def check_access(farmer, org):
    """Check if organization has access to farmer's data"""
    try:
        result = blockchain.check_access(farmer, org)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in check_access endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# CROP SUITABILITY ROUTES - UPDATED WITH EXPLANATIONS
# ============================================================

@app.route('/api/crops/suitability', methods=['POST'])
# @login_required #
def predict_crop_suitability():
    """Predict crop suitability with explanations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Extract all farmer inputs
        location = data.get('location', 'Harare')
        region = data.get('region', 'Midveld')
        soil_type = data.get('soil_type', 'Loam')
        soil_ph = float(data.get('soil_ph', 6.5))
        climate = data.get('climate', 'Subtropical')
        water_mm = data.get('water_mm', 800)
        
        # The farmer's chosen crop
        selected_crop = data.get('crop_type', 'Maize')
        
        hectares = data.get('hectares', 5)
        target_yield = data.get('target_yield', 10)
        budget = data.get('budget', 5000)
        capital = data.get('capital', 3000)
        labour = data.get('labour', 5)
        seedlings = data.get('seedlings', 'Medium')
        weather_days = data.get('weather_days', 7)
        
        logger.info(f"🌾 Predicting for crop: {selected_crop} in {location}")
        
        # Get weather data (live or mock)
        weather = weather_service.get_current_weather(location)
        forecast = weather_service.get_7_day_forecast(location)
        
        # Extract temperature from weather
        if weather.get('success'):
            temp = weather['temperature']
        else:
            temp = 25
        
        # Calculate average rainfall from forecast
        rainfall = water_mm
        if forecast.get('success') and forecast.get('forecast'):
            rain_sum = sum(day.get('total_rain', 0) for day in forecast['forecast'][:7])
            rainfall = rain_sum / 7 if rain_sum > 0 else water_mm
        
        # Get altitude based on location
        altitudes = {
            'Harare': 1500, 'Bulawayo': 1350, 'Mutare': 1120,
            'Binga': 500, 'Murehwa': 1400, 'Gweru': 1450,
            'Masvingo': 1000, 'Chinhoyi': 1200, 'Kadoma': 1150,
            'Kwekwe': 1200
        }
        altitude = altitudes.get(location, 1000)
        
        # Prepare weather data
        weather_data = {
            'temperature': temp,
            'rainfall': rainfall,
            'altitude': altitude,
        }
        
        # Get prediction with explanations from the model
        result = crop_model.predict_with_explanations(
            location=location,
            weather_data=weather_data,
            soil_type=soil_type,
            soil_ph=soil_ph,
            selected_crop=selected_crop,
            forecast_data=forecast.get('forecast', [])[:7] if forecast.get('success') else None
        )
        
        # Add farmer input context to result
        result['farmer_input'] = {
            'location': location,
            'region': region,
            'soil_type': soil_type,
            'soil_ph': soil_ph,
            'climate': climate,
            'water_mm': water_mm,
            'hectares': hectares,
            'target_yield': target_yield,
            'budget': budget,
            'capital': capital,
            'labour': labour,
            'selected_crop': selected_crop
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in crop suitability endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crops/all')
@login_required
def get_all_crops():
    """Get list of all available crops"""
    try:
        return jsonify({
            'success': True,
            'crops': crop_model.crops
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# LAND TENURE ROUTES
# ============================================================

@app.route('/api/land/my-record')
@login_required
def get_my_land_record():
    """Get the current user's land record"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        record = conn.execute(
            'SELECT * FROM land_records WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
            (current_user.id,)
        ).fetchone()
        conn.close()
        
        if record:
            return jsonify({
                'success': True,
                'has_record': True,
                'record': dict(record)
            })
        else:
            return jsonify({
                'success': True,
                'has_record': False
            })
    except Exception as e:
        logger.error(f"Error getting land record: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/land/register', methods=['POST'])
@login_required
def register_land_record():
    """Register a new land record"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        
        # Check if user already has a pending or approved record
        existing = conn.execute(
            'SELECT id FROM land_records WHERE user_id = ? AND status IN ("Pending", "Approved")',
            (current_user.id,)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'You already have a land record pending or approved'})
        
        # Handle document upload (base64)
        document_url = None
        if data.get('document_base64'):
            try:
                # Create uploads directory if it doesn't exist
                upload_dir = 'uploads/land_documents'
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate filename
                filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.get('document_name', 'document')}"
                filepath = os.path.join(upload_dir, filename)
                
                # Decode and save
                file_data = data['document_base64'].split(',')[1] if ',' in data['document_base64'] else data['document_base64']
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(file_data))
                
                document_url = f"/uploads/land_documents/{filename}"
                logger.info(f"Document saved: {filepath}")
            except Exception as e:
                logger.error(f"Error saving document: {str(e)}")
                # Continue without document
        
        # Insert land record
        conn.execute('''
            INSERT INTO land_records (
                user_id, owner_name, national_id, phone, email, deed_number,
                farm_name, plot_number, size_hectares, district, province,
                gps_coordinates, town, tenure_type, use_rights, transfer_rights,
                acquisition_date, boundaries, encumbrances, document_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id,
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
            document_url,
            'Pending'
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Land record registered for user {current_user.id}")
        return jsonify({'success': True, 'message': 'Land registered successfully'})
        
    except Exception as e:
        logger.error(f"Error registering land: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/land/records')
@login_required
def get_land_records():
    """Get all land records (admin sees all, users see their own)"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        
        # Role-based admin check
        is_admin = current_user.role == 'admin'
        
        if is_admin:
            # Admin sees all records
            records = conn.execute('SELECT * FROM land_records ORDER BY created_at DESC').fetchall()
        else:
            # Regular user sees only their records
            records = conn.execute(
                'SELECT * FROM land_records WHERE user_id = ? ORDER BY created_at DESC',
                (current_user.id,)
            ).fetchall()
        
        conn.close()
        
        # Get pending count for admin
        pending_count = 0
        if is_admin:
            conn = get_db_connection()
            pending_count = conn.execute(
                'SELECT COUNT(*) FROM land_records WHERE status = "Pending"'
            ).fetchone()[0]
            conn.close()
        
        return jsonify({
            'success': True,
            'records': [dict(r) for r in records],
            'is_admin': is_admin,
            'pending_count': pending_count
        })
    except Exception as e:
        logger.error(f"Error getting land records: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/land/approve', methods=['POST'])
@login_required
def approve_land():
    """Approve a land record (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        land_id = data.get('land_id')
        
        if not land_id:
            return jsonify({'success': False, 'error': 'Land ID required'}), 400
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE land_records SET status = "Approved", updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (land_id,)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Land record {land_id} approved")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error approving land: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/land/reject', methods=['POST'])
@login_required
def reject_land():
    """Reject a land record (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        land_id = data.get('land_id')
        
        if not land_id:
            return jsonify({'success': False, 'error': 'Land ID required'}), 400
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE land_records SET status = "Rejected", updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (land_id,)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Land record {land_id} rejected")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error rejecting land: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# DATA SOVEREIGNTY ROUTES
# ============================================================

@app.route('/api/crop/record', methods=['POST'])
@login_required
def save_crop_record():
    """Save a crop record for the current user"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO crop_records (
                user_id, crop_type, variety, planting_date, harvest_date,
                land_size, yield_tonnes, fertilizer, watering_method,
                pest_control, notes, success_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id,
            data.get('crop_type'),
            data.get('variety'),
            data.get('planting_date'),
            data.get('harvest_date'),
            float(data.get('land_size', 0)),
            float(data.get('yield_tonnes', 0)),
            data.get('fertilizer'),
            data.get('watering_method'),
            data.get('pest_control'),
            data.get('notes'),
            int(data.get('success_rate', 75))
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Crop record saved'})
    except Exception as e:
        logger.error(f"Error saving crop record: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crop/records')
@login_required
def get_crop_records():
    """Get all crop records for the current user"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        records = conn.execute(
            'SELECT * FROM crop_records WHERE user_id = ? ORDER BY planting_date DESC',
            (current_user.id,)
        ).fetchall()
        conn.close()
        
        # Calculate stats
        total_yield = sum(r['yield_tonnes'] for r in records)
        total_crops = len(records)
        avg_success = sum(r['success_rate'] for r in records) / total_crops if total_crops > 0 else 0
        
        return jsonify({
            'success': True,
            'records': [dict(r) for r in records],
            'total_yield': round(total_yield, 2),
            'total_crops': total_crops,
            'avg_success': f"{round(avg_success)}%"
        })
    except Exception as e:
        logger.error(f"Error getting crop records: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/requests')
@login_required
def get_data_requests():
    """Get data access requests for the current user"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        requests = conn.execute(
            '''SELECT * FROM data_access_requests 
               WHERE farmer_id = ? 
               ORDER BY 
                   CASE WHEN status = 'Pending' THEN 0 ELSE 1 END,
                   requested_at DESC''',
            (current_user.id,)
        ).fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'requests': [dict(r) for r in requests]
        })
    except Exception as e:
        logger.error(f"Error getting data requests: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/grant', methods=['POST'])
@login_required
def grant_data_access():
    """Grant data access to an organization"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        request_id = data.get('request_id')
        
        conn = get_db_connection()
        # Verify the request belongs to the current user
        request = conn.execute(
            'SELECT * FROM data_access_requests WHERE id = ? AND farmer_id = ?',
            (request_id, current_user.id)
        ).fetchone()
        
        if not request:
            conn.close()
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        conn.execute(
            'UPDATE data_access_requests SET status = "Granted", responded_at = CURRENT_TIMESTAMP WHERE id = ?',
            (request_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error granting access: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/deny', methods=['POST'])
@login_required
def deny_data_access():
    """Deny data access to an organization"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        request_id = data.get('request_id')
        
        conn = get_db_connection()
        # Verify the request belongs to the current user
        request = conn.execute(
            'SELECT * FROM data_access_requests WHERE id = ? AND farmer_id = ?',
            (request_id, current_user.id)
        ).fetchone()
        
        if not request:
            conn.close()
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        conn.execute(
            'UPDATE data_access_requests SET status = "Revoked", responded_at = CURRENT_TIMESTAMP WHERE id = ?',
            (request_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error denying access: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/history')
@login_required
def get_data_history():
    """Get access history for the current user"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        history = conn.execute(
            '''SELECT * FROM data_access_requests 
               WHERE farmer_id = ? AND status != 'Pending'
               ORDER BY last_accessed_at DESC''',
            (current_user.id,)
        ).fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'history': [dict(h) for h in history]
        })
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/benefits')
@login_required
def get_data_benefits():
    """Get benefits from data sharing for the current user"""
    try:
        # For demo purposes, return mock benefits
        # In production, this would come from a benefits table
        benefits = [
            {
                'type': 'advisory',
                'title': '🌱 Expert Advisory',
                'description': 'Received personalized crop advice from World Bank experts',
                'value': '✅ 5 consultations',
                'date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'type': 'market',
                'title': '📊 Market Insights',
                'description': 'Access to real-time market prices and demand forecasts',
                'value': '📈 20% price improvement',
                'date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'type': 'input',
                'title': '🧪 Quality Inputs',
                'description': 'Received subsidized fertilizer and improved seeds',
                'value': '💲 $500 value',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        
        return jsonify({
            'success': True,
            'benefits': benefits
        })
    except Exception as e:
        logger.error(f"Error getting benefits: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# CHATBOT ROUTES
# ============================================================

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """
    Multilingual chatbot endpoint
    Supports English, Shona, and Ndebele
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '')
        language = data.get('language', 'English')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Get response from chatbot
        result = chatbot.get_response(message, language)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/advanced', methods=['POST'])
@login_required
def chat_advanced():
    """
    Advanced multilingual chatbot with image analysis
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '')
        language = data.get('language', 'English')
        image_data = data.get('image')
        image_name = data.get('image_name')
        
        # Handle image if present
        image_analysis = None
        if image_data:
            # Save image temporarily for analysis
            import base64
            from datetime import datetime
            import os
            
            # Create uploads directory
            upload_dir = 'uploads/chat_images'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save image
            filename = f"chat_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = os.path.join(upload_dir, filename)
            
            # Decode and save
            file_data = image_data.split(',')[1] if ',' in image_data else image_data
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(file_data))
            
            # Perform basic image analysis (in production, use a real vision model)
            image_analysis = {
                'has_crop': 'crop' in message.lower() or 'plant' in message.lower(),
                'has_pest': 'pest' in message.lower() or 'disease' in message.lower(),
                'filename': filename,
                'url': f"/uploads/chat_images/{filename}"
            }
        
        # If message is empty but image is present
        if not message and image_data:
            message = "Analyze this image for any crop issues, pests, or diseases."
        
        # Get enhanced response
        response = chatbot.get_enhanced_response(message, language, image_analysis)
        
        return jsonify({
            'success': True,
            'response': response,
            'language': language,
            'has_image': bool(image_analysis and image_analysis.get('url')),
            'image_url': image_analysis.get('url') if image_analysis else None
        })
        
    except Exception as e:
        logger.error(f"Error in advanced chat: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# FARMERS MANAGEMENT ROUTES (ADMIN ONLY)
# ============================================================

@app.route('/api/farmers/all')
@login_required
def get_all_farmers():
    """Get all farmers (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        conn = get_db_connection()
        farmers = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'farmers': [dict(f) for f in farmers],
            'is_admin': True
        })
    except Exception as e:
        logger.error(f"Error getting farmers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/farmers/approve', methods=['POST'])
@login_required
def approve_farmer():
    """Approve a farmer (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET is_active = 1, role = "farmer" WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Farmer {user_id} approved")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error approving farmer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/farmers/reject', methods=['POST'])
@login_required
def reject_farmer():
    """Reject a farmer (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET is_active = 0 WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Farmer {user_id} rejected")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error rejecting farmer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/farmers/toggle-status', methods=['POST'])
@login_required
def toggle_farmer_status():
    """Toggle farmer active status (admin only)"""
    try:
        from models.user_model import get_db_connection
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')  # 'active' or 'inactive'
        
        if not user_id or not action:
            return jsonify({'success': False, 'error': 'User ID and action required'}), 400
        
        is_active = 1 if action == 'active' else 0
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET is_active = ? WHERE id = ?',
            (is_active, user_id)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Farmer {user_id} status changed to {action}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error toggling farmer status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/farmers/count')
@login_required
def get_farmer_count():
    """Get farmer count for dashboard"""
    try:
        from models.user_model import get_db_connection
        
        conn = get_db_connection()
        total = conn.execute('SELECT COUNT(*) FROM users WHERE role = "farmer" OR role IS NULL').fetchone()[0]
        active = conn.execute('SELECT COUNT(*) FROM users WHERE (role = "farmer" OR role IS NULL) AND is_active = 1').fetchone()[0]
        pending = conn.execute('SELECT COUNT(*) FROM users WHERE (role = "farmer" OR role IS NULL) AND is_active = 0').fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'total': total,
            'active': active,
            'pending': pending
        })
    except Exception as e:
        logger.error(f"Error getting farmer count: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# MARKET ROUTES
# ============================================================

# Import market models
try:
    from models.market_model import (
        MarketCrop, MarketBuyer, MarketPrice, MarketSupplier, 
        FinancialInstitute, MarketTrend, MarketActivity,
        seed_market_data
    )
except ImportError:
    logger.warning("Market models not found. Market features may be limited.")
    # Define dummy functions to prevent errors
    def seed_market_data():
        pass

# Seed market data on startup
def initialize_market_data():
    try:
        seed_market_data()
        logger.info("✅ Market data initialized")
    except Exception as e:
        logger.warning(f"Market data initialization: {e}")

# Initialize market data when app starts
initialize_market_data()

@app.route('/api/market/crops')
@login_required
def get_market_crops():
    """Get all crops in demand with scores"""
    try:
        crops = MarketCrop.get_all()
        top_crops = MarketCrop.get_top_demand(5)
        return jsonify({
            'success': True,
            'crops': crops,
            'top_demand': top_crops
        })
    except Exception as e:
        logger.error(f"Error getting market crops: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/buyers')
@login_required
def get_market_buyers():
    """Get all buyers"""
    try:
        location = request.args.get('location')
        crop = request.args.get('crop')
        
        if location:
            buyers = MarketBuyer.get_by_location(location)
        elif crop:
            buyers = MarketBuyer.get_by_crop(crop)
        else:
            buyers = MarketBuyer.get_all()
        
        return jsonify({
            'success': True,
            'buyers': buyers,
            'count': len(buyers)
        })
    except Exception as e:
        logger.error(f"Error getting buyers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/prices')
@login_required
def get_market_prices():
    """Get market prices"""
    try:
        crop = request.args.get('crop')
        location = request.args.get('location')
        
        if crop:
            prices = MarketPrice.get_by_crop(crop)
        elif location:
            prices = MarketPrice.get_by_location(location)
        else:
            prices = MarketPrice.get_all()
        
        return jsonify({
            'success': True,
            'prices': prices
        })
    except Exception as e:
        logger.error(f"Error getting prices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/suppliers')
@login_required
def get_market_suppliers():
    """Get input suppliers"""
    try:
        category = request.args.get('category')
        location = request.args.get('location')
        
        if category:
            suppliers = MarketSupplier.get_by_category(category)
        elif location:
            suppliers = MarketSupplier.get_by_location(location)
        else:
            suppliers = MarketSupplier.get_all()
        
        return jsonify({
            'success': True,
            'suppliers': suppliers,
            'categories': ['Seed', 'Fertilizer', 'Equipment', 'Pesticide', 'Feed']
        })
    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/financial')
@login_required
def get_financial_institutes():
    """Get financial institutes"""
    try:
        type_name = request.args.get('type')
        location = request.args.get('location')
        
        if type_name:
            institutes = FinancialInstitute.get_by_type(type_name)
        elif location:
            institutes = FinancialInstitute.get_by_location(location)
        else:
            institutes = FinancialInstitute.get_all()
        
        return jsonify({
            'success': True,
            'institutes': institutes,
            'types': ['Bank', 'Microfinance', 'Cooperative', 'Insurance']
        })
    except Exception as e:
        logger.error(f"Error getting financial institutes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/trends')
@login_required
def get_market_trends():
    """Get market demand trends for charts"""
    try:
        crop = request.args.get('crop')
        location = request.args.get('location', 'Harare')
        months = int(request.args.get('months', 12))
        
        trends = MarketTrend.get_trends(crop, location, months)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'location': location
        })
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/activity')
@login_required
def get_market_activity():
    """Get recent market activity"""
    try:
        limit = int(request.args.get('limit', 10))
        activities = MarketActivity.get_recent(limit)
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        logger.error(f"Error getting activity: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/summary')
@login_required
def get_market_summary():
    """Get market summary statistics"""
    try:
        # Get counts
        crops = MarketCrop.get_all()
        buyers = MarketBuyer.get_all()
        suppliers = MarketSupplier.get_all()
        institutes = FinancialInstitute.get_all()
        
        # Calculate stats
        avg_demand = sum(c['demand_score'] for c in crops) / len(crops) if crops else 0
        top_crop = max(crops, key=lambda x: x['demand_score']) if crops else None
        
        return jsonify({
            'success': True,
            'summary': {
                'total_crops': len(crops),
                'total_buyers': len(buyers),
                'total_suppliers': len(suppliers),
                'total_institutes': len(institutes),
                'avg_demand_score': round(avg_demand, 1),
                'top_crop': top_crop['crop_name'] if top_crop else 'N/A',
                'top_demand_score': top_crop['demand_score'] if top_crop else 0
            }
        })
    except Exception as e:
        logger.error(f"Error getting market summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market/analytics')
def get_market_analytics():
    """Get 7-day rolling market analytics for Harare, Bulawayo, Mutare"""
    try:
        market = request.args.get('market')
        crop = request.args.get('crop')
        if market_analytics_service:
            data = market_analytics_service.get_latest_7day_analytics(market=market, crop=crop)
            return jsonify(data)
        else:
            return jsonify({'success': False, 'error': 'Market analytics service not available'}), 503
    except Exception as e:
        logger.error(f"Error getting 7-day market analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# SETTINGS ROUTES
# ============================================================

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html', user=current_user)

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        conn.execute('''
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
            current_user.id
        ))
        conn.commit()
        conn.close()
        
        # Update session user data
        current_user.first_name = data.get('first_name')
        current_user.last_name = data.get('last_name')
        current_user.phone = data.get('phone')
        current_user.location = data.get('location')
        current_user.bio = data.get('bio')
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        import bcrypt
        from models.user_model import get_db_connection
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (password_hash, current_user.id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# REVIEWS ROUTES
# ============================================================

@app.route('/reviews')
@login_required
def reviews():
    """Reviews and feedback page"""
    return render_template('reviews.html', user=current_user)

@app.route('/api/reviews/submit', methods=['POST'])
@login_required
def submit_review():
    """Submit a review"""
    try:
        from models.user_model import get_db_connection
        import json
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO reviews (
                user_id, user_name, rating, title, content,
                recommend, features, likes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id,
            f"{current_user.first_name} {current_user.last_name}",
            data.get('rating'),
            data.get('title'),
            data.get('content'),
            data.get('recommend'),
            json.dumps(data.get('features', {})),
            0
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Review submitted successfully'})
    except Exception as e:
        logger.error(f"Error submitting review: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews/all')
@login_required
def get_reviews():
    """Get all reviews"""
    try:
        from models.user_model import get_db_connection
        import json
        
        conn = get_db_connection()
        reviews = conn.execute('''
            SELECT * FROM reviews ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        
        result = []
        for r in reviews:
            review_dict = dict(r)
            # Parse features JSON
            if review_dict.get('features'):
                try:
                    review_dict['features'] = json.loads(review_dict['features'])
                except:
                    review_dict['features'] = {}
            result.append(review_dict)
        
        return jsonify({
            'success': True,
            'reviews': result
        })
    except Exception as e:
        logger.error(f"Error getting reviews: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews/like', methods=['POST'])
@login_required
def like_review():
    """Like a review"""
    try:
        from models.user_model import get_db_connection
        
        data = request.get_json()
        review_id = data.get('review_id')
        
        if not review_id:
            return jsonify({'success': False, 'error': 'Review ID required'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE reviews SET likes = likes + 1 WHERE id = ?
        ''', (review_id,))
        conn.commit()
        
        likes = conn.execute('SELECT likes FROM reviews WHERE id = ?', (review_id,)).fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'likes': likes['likes'] if likes else 0
        })
    except Exception as e:
        logger.error(f"Error liking review: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# AGRONOMIST VALIDATION ROUTES
# ============================================================

@app.route('/agronomist/validation')
def agronomist_validation_page():
    """Agronomist human expert evaluation dashboard"""
    return render_template('agronomist_validation.html')

@app.route('/api/agronomist/cases')
def get_agronomist_validation_cases():
    """Get validation cases for agronomist evaluation"""
    try:
        from backend.agronomist_validation_service import agronomist_validation_service
        cases = agronomist_validation_service.get_validation_cases()
        return jsonify({'success': True, 'cases': cases})
    except Exception as e:
        logger.error(f"Error fetching validation cases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agronomist/submit-evaluation', methods=['POST'])
def submit_agronomist_evaluation():
    """Submit a genuine human expert evaluation"""
    try:
        from backend.agronomist_validation_service import agronomist_validation_service
        data = request.get_json() or {}
        case_id = data.get('case_id')
        prediction = data.get('agronomist_prediction')
        expert_id = data.get('expert_id', 'AGRO-ZW-001')
        comments = data.get('comments', '')

        if not case_id or not prediction:
            return jsonify({'success': False, 'error': 'case_id and agronomist_prediction required'}), 400

        result = agronomist_validation_service.submit_evaluation(
            case_id=case_id,
            agronomist_prediction=prediction,
            expert_id=expert_id,
            comments=comments
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error submitting agronomist evaluation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agronomist/metrics')
def get_agronomist_metrics():
    """Get current empirical agronomist agreement metrics"""
    try:
        from backend.agronomist_validation_service import agronomist_validation_service
        metrics = agronomist_validation_service.calculate_metrics()
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        logger.error(f"Error calculating agronomist metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# STATIC FILE ROUTES FOR UPLOADS
# ============================================================

@app.route('/uploads/land_documents/<filename>')
def serve_land_document(filename):
    """Serve uploaded land documents"""
    return send_from_directory('uploads/land_documents', filename)

@app.route('/uploads/chat_images/<filename>')
def serve_chat_image(filename):
    """Serve uploaded chat images"""
    return send_from_directory('uploads/chat_images', filename)


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == '__main__':
    logger.info("🚀 Starting AgricLedger Flask Application...")
    logger.info(f"📊 Blockchain connected: {blockchain.w3.is_connected() if blockchain.w3 else False}")
    
    # Check weather API status
    weather_status = weather_service.test_api_connection()
    if weather_status.get('success'):
        logger.info("🌤️ Weather API: Connected")
    else:
        logger.warning(f"🌤️ Weather API: {weather_status.get('error', 'Not connected - using mock data')}")
    
    # Create uploads directory
    os.makedirs('uploads/land_documents', exist_ok=True)
    os.makedirs('uploads/chat_images', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)