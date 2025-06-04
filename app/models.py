from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), default='buyer')  # buyer, seller, both
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    rice_listings = db.relationship('RiceListing', backref='seller', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.full_name}>'

class RiceListing(db.Model):
    """Rice listing model for marketplace"""
    __tablename__ = 'rice_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rice_type = db.Column(db.String(50), nullable=False)  # Basmati, Sona Masoori, etc.
    variety = db.Column(db.String(100), nullable=True)  # Specific variety name
    quantity = db.Column(db.Float, nullable=False)  # In kilograms
    price_per_kg = db.Column(db.Float, nullable=False)
    quality_grade = db.Column(db.String(20), default='A')  # A, B, C grades
    harvest_date = db.Column(db.Date, nullable=True)
    processing_type = db.Column(db.String(50), default='Raw')  # Raw, Steamed, Parboiled
    organic = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    minimum_order = db.Column(db.Float, default=10.0)  # Minimum order in kg
    storage_location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<RiceListing {self.rice_type} - {self.quantity}kg>'
    
    @property
    def total_value(self):
        """Calculate total value of the listing"""
        return self.quantity * self.price_per_kg

class ChatMessage(db.Model):
    """Chat message model for AI assistant"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='general')  # general, price_inquiry, market_analysis
    context_data = db.Column(db.JSON, nullable=True)  # Store additional context as JSON
    satisfaction_rating = db.Column(db.Integer, nullable=True)  # 1-5 rating
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<ChatMessage {self.id} - User {self.user_id}>'

class MarketAnalysis(db.Model):
    """Market analysis and price trends"""
    __tablename__ = 'market_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    rice_type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    price_trend = db.Column(db.String(20), nullable=False)  # increasing, decreasing, stable
    demand_level = db.Column(db.String(20), nullable=False)  # high, medium, low
    supply_level = db.Column(db.String(20), nullable=False)  # high, medium, low
    market_sentiment = db.Column(db.String(20), default='neutral')  # bullish, bearish, neutral
    insights = db.Column(db.Text, nullable=True)
    data_source = db.Column(db.String(100), default='AI Analysis')
    confidence_score = db.Column(db.Float, default=0.8)  # 0.0 to 1.0
    analysis_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<MarketAnalysis {self.rice_type} - {self.region}>'
    
    @classmethod
    def get_latest_analysis(cls, rice_type=None, region=None):
        """Get the latest market analysis for given parameters"""
        query = cls.query
        if rice_type:
            query = query.filter_by(rice_type=rice_type)
        if region:
            query = query.filter_by(region=region)
        return query.order_by(cls.analysis_date.desc()).first()

class PriceHistory(db.Model):
    """Historical price data for trends and analysis"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    rice_type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    market_volume = db.Column(db.Float, nullable=True)  # Total volume traded
    quality_grade = db.Column(db.String(20), default='A')
    data_source = db.Column(db.String(100), default='Market Survey')
    recorded_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<PriceHistory {self.rice_type} - ₹{self.price_per_kg}/kg>'
