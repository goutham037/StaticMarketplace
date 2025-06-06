import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
babel = Babel()
login_manager = LoginManager()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///greenbridge.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Babel configuration
    app.config['LANGUAGES'] = {
        'en': 'English',
        'hi': 'हिंदी',
        'te': 'తెలుగు'
    }
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    
    # Initialize extensions with app
    db.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Babel locale selector
    @babel.localeselector
    def get_locale():
        from flask import session, request
        # 1. If a user is logged in and has set a language preference, use that
        if 'language' in session:
            return session['language']
        # 2. Otherwise, try to guess the language from the user accept header
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'
    
    # Create database tables
    with app.app_context():
        # Import models here to avoid circular imports
        import models
        db.create_all()
        logging.info("Database tables created successfully")
        
        # Create sample data for demo
        models.create_sample_data()
    
    # Register routes after app creation
    with app.app_context():
        import routes
    
    # Context processors
    @app.context_processor
    def inject_config():
        return dict(LANGUAGES=app.config['LANGUAGES'])
    
    return app

# Create the app instance
app = create_app()
