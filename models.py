from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), default='buyer')  # buyer or seller
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    rice_listings = db.relationship('RiceListing', backref='seller', lazy=True)
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_distance_to(self, other_lat, other_lng):
        """Calculate distance to another location in kilometers"""
        if not self.latitude or not self.longitude:
            return None
        
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [self.latitude, self.longitude, other_lat, other_lng])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'mobile_number': self.mobile_number,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'user_type': self.user_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RiceListing(db.Model):
    """Rice listing model for marketplace"""
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rice_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in kg
    price_per_kg = db.Column(db.Float, nullable=False)
    quality_grade = db.Column(db.String(20), default='A')
    harvest_date = db.Column(db.Date)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert listing to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'rice_type': self.rice_type,
            'quantity': self.quantity,
            'price_per_kg': self.price_per_kg,
            'quality_grade': self.quality_grade,
            'harvest_date': self.harvest_date.isoformat() if self.harvest_date else None,
            'description': self.description,
            'image_url': self.image_url,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'seller': self.seller.to_dict() if self.seller else None
        }

class ChatMessage(db.Model):
    """Chat message model for AI assistant"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert chat message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'message': self.message,
            'response': self.response,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MarketAnalysis(db.Model):
    """Market analysis model for tracking rice prices and trends"""
    id = db.Column(db.Integer, primary_key=True)
    rice_type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    price_trend = db.Column(db.String(20))  # increasing, decreasing, stable
    demand_level = db.Column(db.String(20))  # high, medium, low
    supply_level = db.Column(db.String(20))  # high, medium, low
    analysis_data = db.Column(db.Text)  # JSON data for detailed analysis
    date_analyzed = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_analysis_data(self):
        """Get parsed analysis data"""
        if self.analysis_data:
            return json.loads(self.analysis_data)
        return {}
    
    def set_analysis_data(self, data):
        """Set analysis data as JSON"""
        self.analysis_data = json.dumps(data)

def create_sample_data():
    """Create sample data for demo purposes"""
    try:
        # Check if sample data already exists
        if User.query.first():
            return
        
        # Sample locations in India (lat, lng)
        locations = [
            ("Hyderabad, Telangana", 17.3850, 78.4867),
            ("Warangal, Telangana", 17.9689, 79.5941),
            ("Karimnagar, Telangana", 18.4386, 79.1288),
            ("Nizamabad, Telangana", 18.6725, 78.0941),
            ("Khammam, Telangana", 17.2473, 80.1514),
            ("Bangalore, Karnataka", 12.9716, 77.5946),
            ("Chennai, Tamil Nadu", 13.0827, 80.2707)
        ]
        
        # Create sample users (farmers/sellers)
        farmers = []
        for i, (location, lat, lng) in enumerate(locations):
            farmer = User(
                full_name=f"Farmer {i+1}",
                mobile_number=f"90000{i+10001:05d}",
                location=location,
                latitude=lat,
                longitude=lng,
                user_type='seller'
            )
            farmer.set_password('password123')
            farmers.append(farmer)
            db.session.add(farmer)
        
        # Create a sample buyer
        buyer = User(
            full_name="Demo Buyer",
            mobile_number="9000000001",
            location="Hyderabad, Telangana",
            latitude=17.3850,
            longitude=78.4867,
            user_type='buyer'
        )
        buyer.set_password('password123')
        db.session.add(buyer)
        
        db.session.commit()
        
        # Create sample rice listings
        rice_types = ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice']
        prices = [65, 45, 42, 55]  # prices per kg
        
        for farmer in farmers:
            for i, (rice_type, price) in enumerate(zip(rice_types, prices)):
                if i % 2 == farmer.id % 2:  # Create varied listings
                    listing = RiceListing(
                        seller_id=farmer.id,
                        rice_type=rice_type,
                        quantity=1000 + (farmer.id * 500),  # Varied quantities
                        price_per_kg=price + (farmer.id % 3) * 2,  # Slight price variations
                        quality_grade='A',
                        description=f"High quality {rice_type} from {farmer.location}",
                        is_available=True
                    )
                    db.session.add(listing)
        
        # Create sample market analysis
        for rice_type, base_price in zip(rice_types, prices):
            analysis = MarketAnalysis(
                rice_type=rice_type,
                region="Telangana",
                average_price=base_price,
                price_trend="stable",
                demand_level="high",
                supply_level="medium"
            )
            analysis.set_analysis_data({
                "weekly_trend": [base_price-2, base_price-1, base_price, base_price+1, base_price],
                "forecast": [base_price+1, base_price+2, base_price+1],
                "market_insights": f"{rice_type} shows stable pricing with good demand."
            })
            db.session.add(analysis)
        
        db.session.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.session.rollback()
