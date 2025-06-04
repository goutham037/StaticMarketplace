# GreenBridge - Multilingual Rice E-Commerce Platform

## Project Overview
A multilingual e-commerce platform connecting rice buyers with farmers, supporting English, Hindi, and Telugu languages.

## Features Implemented

### Buyer Dashboard
- Location-based farmer search with map integration
- Visual rice type selection (Basmati, Sona Masoori, Brown Rice)
- Quantity specification with unit conversion (kg/quintals/tons)
- Nearby farmer listing with distance calculation
- Contact farmer functionality

### Authentication & User Management
- User registration and login system
- Flask-Login integration for secure authentication
- Protected routes with @login_required decorator
- User model with password hashing

### Multilingual Support
- Complete translations for Hindi and Telugu
- Language switching functionality
- Translated content includes:
  - UI elements
  - Rice type descriptions
  - Error messages
  - Location and quantity selectors

### Database Models
- User: Profile management with location tracking
- RiceListing: Rice product listings
- ChatMessage: User communication
- MarketAnalysis: Price trends and market insights

## Technical Stack
- Flask web framework
- SQLAlchemy for database management
- Flask-Login for authentication
- Flask-Babel for internationalization
- Leaflet.js for map integration

## Project Structure
```
project2/
├── app/
│   ├── __init__.py          # Application factory and extensions
│   ├── models.py            # Database models
│   ├── routes/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── buyer.py
│   │   ├── seller.py
│   │   └── ai.py
│   ├── templates/
│   │   ├── base.html
│   │   └── buyer/
│   │       └── dashboard.html
│   ├── translations/
│   │   ├── hi/             # Hindi translations
│   │   └── te/             # Telugu translations
│   └── static/
│       └── images/         # Rice type images
```

## Recent Updates
1. Implemented Flask-Login integration
   - Added LoginManager initialization
   - Updated User model with UserMixin
   - Configured login views and messages

2. Enhanced Buyer Dashboard
   - Geolocation support
   - Interactive map integration
   - Rice type selection cards
   - Quantity unit conversion

3. Added Multilingual Support
   - Complete Hindi translations
   - Complete Telugu translations
   - Language selection functionality

## Setup Instructions
1. Install required packages:
```bash
pip install flask flask-sqlalchemy flask-babel flask-login python-dotenv
```

2. Set up environment variables:
- SECRET_KEY
- SQLALCHEMY_DATABASE_URI

3. Initialize the database:
```bash
flask db upgrade
```

4. Run the application:
```bash
flask run
```

## Next Steps
- Implement actual farmer search based on location
- Add real-time chat functionality
- Integrate payment gateway
- Add order management system
- Implement AI-powered market analysis 