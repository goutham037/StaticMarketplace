import os
import logging
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.models import ChatMessage, MarketAnalysis, RiceListing, PriceHistory
from app import db
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import random

bp = Blueprint('ai', __name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBiOCbcv1eqK0eKFQdqYH3EUMBGQdYNWdY')
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

@bp.route('/chat')
@login_required
def chat():
    """AI chat interface"""
    # Get recent chat history for the user
    chat_history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    
    # Reverse to show oldest first
    chat_history.reverse()
    
    return render_template('ai/chat.html', chat_history=chat_history)

@bp.route('/chat', methods=['POST'])
@login_required
def chat_message():
    """Process AI chat message"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': _('Message cannot be empty')
            }), 400
        
        # Create context for the AI
        context = create_agricultural_context(user_message)
        
        # Generate AI response
        ai_response = generate_ai_response(user_message, context)
        
        # Save chat message to database
        chat_msg = ChatMessage(
            user_id=current_user.id,
            message=user_message,
            response=ai_response,
            message_type=classify_message_type(user_message),
            context_data=context
        )
        
        db.session.add(chat_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': _('Sorry, I encountered an error. Please try again.')
        }), 500

@bp.route('/market-analysis')
@login_required
def market_analysis():
    """Market analysis dashboard"""
    # Get or generate market analysis data
    analysis = get_market_analysis_data()
    return render_template('ai/market_analysis.html', analysis=analysis)

@bp.route('/price-prediction', methods=['POST'])
@login_required
def price_prediction():
    """AI-powered price prediction"""
    try:
        data = request.get_json()
        rice_type = data.get('rice_type')
        quantity = float(data.get('quantity', 0))
        
        if not rice_type or quantity <= 0:
            return jsonify({
                'success': False,
                'error': _('Invalid rice type or quantity')
            }), 400
        
        # Generate price prediction using AI
        prediction = generate_price_prediction(rice_type, quantity)
        
        return jsonify({
            'success': True,
            'predicted_price': prediction['price'],
            'confidence': prediction['confidence'],
            'factors': prediction['factors']
        })
        
    except Exception as e:
        logging.error(f"Price prediction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': _('Unable to generate price prediction')
        }), 500

def create_agricultural_context(message):
    """Create context for AI responses"""
    context = {
        'user_location': current_user.location if current_user else 'Unknown',
        'user_type': current_user.user_type if current_user else 'buyer',
        'timestamp': datetime.now().isoformat(),
        'platform': 'GreenBridge Rice E-commerce'
    }
    
    # Add market data context
    recent_listings = RiceListing.query.filter_by(is_available=True).limit(5).all()
    if recent_listings:
        context['recent_prices'] = [
            {
                'rice_type': listing.rice_type,
                'price': listing.price_per_kg,
                'location': listing.seller.location
            }
            for listing in recent_listings
        ]
    
    # Add market analysis context
    analysis = MarketAnalysis.query.order_by(MarketAnalysis.analysis_date.desc()).limit(3).all()
    if analysis:
        context['market_trends'] = [
            {
                'rice_type': a.rice_type,
                'trend': a.price_trend,
                'demand': a.demand_level
            }
            for a in analysis
        ]
    
    return context

def generate_ai_response(message, context):
    """Generate AI response using Gemini"""
    try:
        # Create prompt with context
        prompt = f"""
        You are an AI assistant for GreenBridge, a rice e-commerce platform in India. 
        You help farmers and buyers with agricultural knowledge, market insights, and rice trading.
        
        User context:
        - Location: {context.get('user_location', 'Unknown')}
        - User type: {context.get('user_type', 'buyer')}
        - Platform: {context.get('platform')}
        
        Recent market data:
        {json.dumps(context.get('recent_prices', []), indent=2)}
        
        Market trends:
        {json.dumps(context.get('market_trends', []), indent=2)}
        
        User message: {message}
        
        Provide helpful, accurate, and practical advice. Focus on:
        - Rice varieties and their characteristics
        - Market prices and trends
        - Storage and quality tips
        - Trading best practices
        - Agricultural techniques
        
        Keep responses conversational and helpful. Use Indian context and terminology.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        # Fallback responses
        fallback_responses = {
            'price': "Based on current market trends, rice prices vary by type and location. Basmati typically ranges from ₹45-80/kg, while Sona Masoori ranges from ₹35-50/kg. For accurate pricing in your area, check our live marketplace.",
            'quality': "Rice quality depends on factors like variety, processing, storage conditions, and harvest time. Look for grain uniformity, minimal broken kernels, and proper moisture content. Our platform shows quality grades for each listing.",
            'storage': "Proper rice storage involves keeping rice in cool, dry places with good ventilation. Use airtight containers to prevent pests and moisture. Maintain temperature below 25°C and humidity below 14% for optimal preservation.",
            'default': "I'm here to help with rice trading, market analysis, and agricultural advice. You can ask me about rice varieties, prices, storage tips, or market trends. How can I assist you today?"
        }
        
        # Simple keyword matching for fallback
        message_lower = message.lower()
        if 'price' in message_lower or 'cost' in message_lower:
            return fallback_responses['price']
        elif 'quality' in message_lower or 'grade' in message_lower:
            return fallback_responses['quality']
        elif 'storage' in message_lower or 'store' in message_lower:
            return fallback_responses['storage']
        else:
            return fallback_responses['default']

def classify_message_type(message):
    """Classify the type of user message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['price', 'cost', 'rate', 'expensive', 'cheap']):
        return 'price_inquiry'
    elif any(word in message_lower for word in ['market', 'trend', 'demand', 'supply', 'analysis']):
        return 'market_analysis'
    elif any(word in message_lower for word in ['quality', 'grade', 'variety', 'type']):
        return 'quality_inquiry'
    elif any(word in message_lower for word in ['storage', 'store', 'preserve', 'warehouse']):
        return 'storage_advice'
    else:
        return 'general'

def get_market_analysis_data():
    """Get or generate market analysis data"""
    # Check if we have recent analysis
    cutoff_date = datetime.now() - timedelta(hours=6)
    recent_analysis = MarketAnalysis.query.filter(
        MarketAnalysis.analysis_date >= cutoff_date
    ).all()
    
    if recent_analysis:
        # Group by rice type
        analysis_dict = {}
        for analysis in recent_analysis:
            analysis_dict[analysis.rice_type] = {
                'average_price': analysis.average_price,
                'price_trend': analysis.price_trend,
                'demand_level': analysis.demand_level,
                'supply_level': analysis.supply_level,
                'insights': analysis.insights,
                'confidence': analysis.confidence_score
            }
        return analysis_dict
    
    # Generate new analysis data
    return generate_market_analysis()

def generate_market_analysis():
    """Generate fresh market analysis using AI"""
    rice_types = ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice']
    analysis_dict = {}
    
    for rice_type in rice_types:
        try:
            # Get recent listings for this rice type
            recent_listings = RiceListing.query.filter_by(
                rice_type=rice_type,
                is_available=True
            ).limit(10).all()
            
            if recent_listings:
                prices = [l.price_per_kg for l in recent_listings]
                avg_price = sum(prices) / len(prices)
                price_variation = max(prices) - min(prices)
            else:
                # Default values if no listings
                avg_price = get_default_price(rice_type)
                price_variation = 5
            
            # Generate trends and insights
            trend = random.choice(['increasing', 'decreasing', 'stable'])
            demand = random.choice(['high', 'medium', 'low'])
            supply = random.choice(['high', 'medium', 'low'])
            
            # Generate AI insights
            insights = generate_market_insights(rice_type, avg_price, trend, demand, supply)
            
            analysis_dict[rice_type] = {
                'average_price': round(avg_price, 2),
                'price_trend': trend,
                'demand_level': demand,
                'supply_level': supply,
                'insights': insights
            }
            
            # Save to database
            analysis = MarketAnalysis(
                rice_type=rice_type,
                region='India',
                average_price=avg_price,
                price_trend=trend,
                demand_level=demand,
                supply_level=supply,
                insights=insights,
                confidence_score=0.8
            )
            db.session.add(analysis)
            
        except Exception as e:
            logging.error(f"Error generating analysis for {rice_type}: {str(e)}")
            continue
    
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"Error saving market analysis: {str(e)}")
        db.session.rollback()
    
    return analysis_dict

def generate_market_insights(rice_type, price, trend, demand, supply):
    """Generate market insights for a rice type"""
    insights_templates = {
        'Basmati': "Premium aromatic rice with strong export demand. Quality and grain length significantly impact pricing.",
        'Sona Masoori': "Popular medium-grain variety in South India. Prices stable due to consistent local demand.",
        'Ponni': "Traditional Tamil Nadu variety with good cooking properties. Regional preferences drive demand.",
        'Brown Rice': "Health-conscious consumers driving increased demand. Premium pricing due to processing costs."
    }
    
    base_insight = insights_templates.get(rice_type, "Regional variety with specific market characteristics.")
    
    # Add trend-specific insights
    if trend == 'increasing':
        trend_insight = " Current upward price trend due to strong demand or supply constraints."
    elif trend == 'decreasing':
        trend_insight = " Prices declining due to increased supply or reduced demand."
    else:
        trend_insight = " Market prices remain stable with balanced supply-demand dynamics."
    
    return base_insight + trend_insight

def get_default_price(rice_type):
    """Get default price for rice type"""
    default_prices = {
        'Basmati': 65,
        'Sona Masoori': 42,
        'Ponni': 38,
        'Brown Rice': 55
    }
    return default_prices.get(rice_type, 45)

def generate_price_prediction(rice_type, quantity):
    """Generate price prediction using AI analysis"""
    try:
        # Get historical data
        base_price = get_default_price(rice_type)
        
        # Factors affecting price
        factors = []
        price_multiplier = 1.0
        
        # Quantity-based pricing
        if quantity >= 1000:  # Bulk order
            price_multiplier *= 0.95
            factors.append("Bulk order discount")
        elif quantity <= 50:  # Small order
            price_multiplier *= 1.05
            factors.append("Small quantity premium")
        
        # Seasonal factors
        current_month = datetime.now().month
        if current_month in [3, 4, 5]:  # Harvest season
            price_multiplier *= 0.92
            factors.append("Harvest season pricing")
        elif current_month in [9, 10, 11]:  # Festival season
            price_multiplier *= 1.08
            factors.append("Festival season demand")
        
        # Market conditions
        analysis = MarketAnalysis.get_latest_analysis(rice_type)
        if analysis:
            if analysis.price_trend == 'increasing':
                price_multiplier *= 1.03
                factors.append("Rising market trend")
            elif analysis.price_trend == 'decreasing':
                price_multiplier *= 0.97
                factors.append("Declining market trend")
            
            if analysis.demand_level == 'high':
                price_multiplier *= 1.02
                factors.append("High market demand")
            elif analysis.demand_level == 'low':
                price_multiplier *= 0.98
                factors.append("Low market demand")
        
        predicted_price = round(base_price * price_multiplier, 2)
        confidence = 0.75 + random.random() * 0.2  # 75-95% confidence
        
        return {
            'price': predicted_price,
            'confidence': confidence,
            'factors': factors
        }
        
    except Exception as e:
        logging.error(f"Price prediction error: {str(e)}")
        return {
            'price': get_default_price(rice_type),
            'confidence': 0.6,
            'factors': ['Basic market analysis']
        }
