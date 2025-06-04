import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone, date
import json
import math

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///greenbridge.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Language configuration
app.config['LANGUAGES'] = {
    'en': 'English',
    'hi': 'हिंदी',
    'te': 'తెలుగు'
}

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), default='buyer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    rice_listings = db.relationship('RiceListing', backref='seller', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_distance_to(self, other_lat, other_lng):
        if not self.latitude or not self.longitude:
            return float('inf')
        return calculate_distance(self.latitude, self.longitude, other_lat, other_lng)

class RiceListing(db.Model):
    __tablename__ = 'rice_listings'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rice_type = db.Column(db.String(50), nullable=False)
    variety = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    quality_grade = db.Column(db.String(20), default='A')
    harvest_date = db.Column(db.Date, nullable=True)
    processing_type = db.Column(db.String(50), default='Raw')
    organic = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    minimum_order = db.Column(db.Float, default=10.0)
    storage_location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def total_value(self):
        return self.quantity * self.price_per_kg

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='general')
    context_data = db.Column(db.JSON, nullable=True)
    satisfaction_rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class MarketAnalysis(db.Model):
    __tablename__ = 'market_analysis'
    id = db.Column(db.Integer, primary_key=True)
    rice_type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    price_trend = db.Column(db.String(20), nullable=False)
    demand_level = db.Column(db.String(20), nullable=False)
    supply_level = db.Column(db.String(20), nullable=False)
    market_sentiment = db.Column(db.String(20), default='neutral')
    insights = db.Column(db.Text, nullable=True)
    data_source = db.Column(db.String(100), default='AI Analysis')
    confidence_score = db.Column(db.Float, default=0.8)
    analysis_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_ai_response(message, user):
    """Simple AI response for demonstration"""
    responses = {
        'price': f"Based on current market trends, rice prices are stable. For {user.location}, expect prices around ₹40-60 per kg depending on variety.",
        'market': "The rice market is currently experiencing steady demand with seasonal variations. Basmati and premium varieties show strong performance.",
        'weather': "Weather conditions are favorable for rice cultivation this season. Monitor moisture levels and consider organic farming practices.",
        'default': "I'm here to help with rice trading, market analysis, and farming advice. What specific information do you need?"
    }
    
    message_lower = message.lower()
    if any(word in message_lower for word in ['price', 'cost', 'rate']):
        return responses['price']
    elif any(word in message_lower for word in ['market', 'demand', 'supply']):
        return responses['market']
    elif any(word in message_lower for word in ['weather', 'climate', 'season']):
        return responses['weather']
    else:
        return responses['default']

def create_sample_data():
    """Create sample data for demonstration"""
    try:
        # Check if sample data already exists
        if User.query.first():
            return
        
        # Create sample users
        farmer1 = User(
            full_name="Ravi Kumar",
            mobile_number="9876543210",
            location="Guntur, Andhra Pradesh",
            latitude=16.2931,
            longitude=80.4374,
            user_type="seller"
        )
        farmer1.set_password("password123")
        
        buyer1 = User(
            full_name="Priya Sharma",
            mobile_number="9876543211",
            location="Hyderabad, Telangana", 
            latitude=17.3850,
            longitude=78.4867,
            user_type="buyer"
        )
        buyer1.set_password("password123")
        
        db.session.add(farmer1)
        db.session.add(buyer1)
        db.session.commit()
        
        # Create sample rice listings
        listing1 = RiceListing(
            seller_id=farmer1.id,
            rice_type="Basmati",
            variety="1121 Golden Sella",
            quantity=1000.0,
            price_per_kg=55.0,
            quality_grade="A",
            harvest_date=date(2024, 11, 15),
            processing_type="Steamed",
            organic=False,
            description="Premium quality Basmati rice, aged for 2 years",
            minimum_order=50.0,
            storage_location="Climate controlled warehouse"
        )
        
        listing2 = RiceListing(
            seller_id=farmer1.id,
            rice_type="Sona Masoori",
            variety="HMT",
            quantity=500.0,
            price_per_kg=42.0,
            quality_grade="A",
            harvest_date=date(2024, 10, 20),
            processing_type="Raw",
            organic=True,
            description="Organic Sona Masoori rice from sustainable farming",
            minimum_order=25.0,
            storage_location="Traditional storage"
        )
        
        db.session.add(listing1)
        db.session.add(listing2)
        db.session.commit()
        
        # Create sample market analysis
        analysis1 = MarketAnalysis(
            rice_type="Basmati",
            region="Andhra Pradesh",
            average_price=55.0,
            price_trend="stable",
            demand_level="high",
            supply_level="medium",
            market_sentiment="bullish",
            insights="Strong export demand driving prices upward. Premium varieties showing exceptional performance."
        )
        
        analysis2 = MarketAnalysis(
            rice_type="Sona Masoori",
            region="Telangana",
            average_price=42.0,
            price_trend="increasing",
            demand_level="medium",
            supply_level="high",
            market_sentiment="neutral",
            insights="Local demand steady with good harvest this season. Organic varieties commanding premium prices."
        )
        
        db.session.add(analysis1)
        db.session.add(analysis2)
        db.session.commit()
        
        logging.info("Sample data created successfully")
        
    except Exception as e:
        logging.error(f"Error creating sample data: {e}")
        db.session.rollback()

# Routes
@app.before_request
def before_request():
    g.locale = session.get('language', 'en')

@app.route('/')
def index():
    total_farmers = User.query.filter_by(user_type='seller').count()
    total_listings = RiceListing.query.filter_by(is_available=True).count()
    rice_types = db.session.query(RiceListing.rice_type).distinct().count()
    
    return render_template('index.html',
                         total_farmers=total_farmers,
                         total_listings=total_listings,
                         rice_types=rice_types)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        mobile_number = request.form.get('mobile_number')
        location = request.form.get('location')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'buyer')
        
        # Check if user already exists
        if User.query.filter_by(mobile_number=mobile_number).first():
            flash('Mobile number already registered')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            full_name=full_name,
            mobile_number=mobile_number,
            location=location,
            user_type=user_type
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        password = request.form.get('password')
        
        user = User.query.filter_by(mobile_number=mobile_number).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.user_type == 'seller':
                return redirect(next_page or url_for('seller_dashboard'))
            else:
                return redirect(next_page or url_for('buyer_dashboard'))
        else:
            flash('Invalid mobile number or password')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    # Get nearby listings
    listings = RiceListing.query.filter_by(is_available=True).limit(10).all()
    
    # Get market analysis
    analysis = {}
    for rice_type in ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice']:
        market_data = MarketAnalysis.query.filter_by(rice_type=rice_type).first()
        if market_data:
            analysis[rice_type] = market_data
    
    return render_template('buyer/dashboard.html', listings=listings, analysis=analysis)

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    listings = RiceListing.query.filter_by(seller_id=current_user.id).all()
    total_revenue = sum(listing.total_value() for listing in listings if listing.is_available)
    
    return render_template('seller/dashboard.html', 
                         listings=listings, 
                         total_revenue=total_revenue)

@app.route('/seller/new-listing', methods=['GET', 'POST'])
@login_required
def new_listing():
    if request.method == 'POST':
        listing = RiceListing(
            seller_id=current_user.id,
            rice_type=request.form.get('rice_type'),
            variety=request.form.get('variety'),
            quantity=float(request.form.get('quantity', 0)),
            price_per_kg=float(request.form.get('price_per_kg', 0)),
            quality_grade=request.form.get('quality_grade', 'A'),
            harvest_date=datetime.strptime(request.form.get('harvest_date'), '%Y-%m-%d').date() if request.form.get('harvest_date') else None,
            processing_type=request.form.get('processing_type', 'Raw'),
            organic=request.form.get('organic') == 'on',
            description=request.form.get('description'),
            minimum_order=float(request.form.get('minimum_order', 10)),
            storage_location=request.form.get('storage_location')
        )
        
        db.session.add(listing)
        db.session.commit()
        
        flash('Listing created successfully')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('seller/new_listing.html')

@app.route('/ai/chat')
@login_required
def chat():
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(10).all()
    return render_template('ai/chat.html', messages=messages)

@app.route('/ai/chat', methods=['POST'])
@login_required
def chat_message():
    data = request.get_json()
    message = data.get('message', '')
    
    # Get AI response
    response = get_ai_response(message, current_user)
    
    # Save chat message
    chat_msg = ChatMessage(
        user_id=current_user.id,
        message=message,
        response=response,
        message_type='general'
    )
    
    db.session.add(chat_msg)
    db.session.commit()
    
    return jsonify({
        'response': response,
        'timestamp': chat_msg.created_at.isoformat()
    })

@app.route('/ai/market-analysis')
@login_required
def market_analysis():
    # Get market analysis data
    analysis = {}
    rice_types = ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice']
    
    for rice_type in rice_types:
        market_data = MarketAnalysis.query.filter_by(rice_type=rice_type).first()
        if market_data:
            analysis[rice_type] = market_data
    
    return render_template('ai/market_analysis.html', analysis=analysis)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    rice_type = request.args.get('rice_type', '')
    max_price = request.args.get('max_price', type=float)
    
    # Build query
    listings_query = RiceListing.query.filter_by(is_available=True)
    
    if rice_type:
        listings_query = listings_query.filter(RiceListing.rice_type == rice_type)
    
    if max_price:
        listings_query = listings_query.filter(RiceListing.price_per_kg <= max_price)
    
    if query:
        listings_query = listings_query.filter(
            RiceListing.description.contains(query) |
            RiceListing.variety.contains(query)
        )
    
    listings = listings_query.all()
    
    return render_template('buyer/search.html', 
                         listings=listings, 
                         query=query,
                         rice_type=rice_type,
                         max_price=max_price)

@app.route('/set-language/<language>')
def set_language(language):
    if language in app.config['LANGUAGES']:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

# Context processors
@app.context_processor
def inject_config():
    return dict(LANGUAGES=app.config['LANGUAGES'])

# Create tables and sample data
with app.app_context():
    db.create_all()
    create_sample_data()
    logging.info("Database initialized successfully")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)