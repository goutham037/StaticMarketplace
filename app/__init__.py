import os
import logging
from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, get_locale
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
babel = Babel()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///greenbridge.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Babel configuration for multilingual support
    app.config['LANGUAGES'] = {
        'en': 'English',
        'hi': 'हिंदी',
        'te': 'తెలుగు'
    }
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    
    # Configure Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    @babel.localeselector
    def get_locale():
        # 1. Check if language is set in session
        if 'language' in session:
            return session['language']
        # 2. Check user's preferred language
        # 3. Fall back to request's best match
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
    
    # Register blueprints
    from app.routes import main, auth, buyer, seller, ai
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(buyer.bp, url_prefix='/buyer')
    app.register_blueprint(seller.bp, url_prefix='/seller')
    app.register_blueprint(ai.bp, url_prefix='/ai')
    
    # Create database tables
    with app.app_context():
        from app.models import User, RiceListing, ChatMessage, MarketAnalysis
        db.create_all()
        logging.info("Database tables created successfully")
    
    # Global template variables
    @app.context_processor
    def inject_globals():
        return {
            'languages': app.config['LANGUAGES'],
            'current_language': get_locale()
        }
    
    return app
