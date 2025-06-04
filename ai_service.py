import os
import google.generativeai as genai
from models import RiceListing, MarketAnalysis, User, db
import json
import random
from datetime import datetime, timedelta

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "default_key"))

def get_ai_response(message, user):
    """Get AI response using Gemini API"""
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create context for the AI
        context = f"""
        You are an AI assistant for GreenBridge, a rice e-commerce platform connecting farmers and buyers in India.
        
        User Information:
        - Name: {user.full_name}
        - Type: {user.user_type}
        - Location: {user.location}
        
        You can help with:
        - Rice trading and market information
        - Price trends and predictions
        - Quality assessment
        - Storage and handling tips
        - Agricultural best practices
        - Platform features and navigation
        
        Please provide helpful, accurate information related to rice trading and agriculture.
        Keep responses concise but informative. Use Indian context and terminology.
        
        User message: {message}
        """
        
        # Generate response
        response = model.generate_content(context)
        
        return response.text
        
    except Exception as e:
        print(f"Error generating AI response: {e}")
        
        # Fallback responses based on message content
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['price', 'cost', 'rate']):
            return "Current rice prices vary by type and region. Basmati ranges from ₹60-80/kg, Sona Masoori ₹40-50/kg, and Brown rice ₹50-60/kg. Prices are influenced by quality, harvest season, and market demand."
        
        elif any(word in message_lower for word in ['quality', 'grade']):
            return "Rice quality is typically graded as A, B, or C based on factors like broken grain percentage, moisture content, and purity. Grade A has <5% broken grains, optimal moisture (12-14%), and minimal impurities."
        
        elif any(word in message_lower for word in ['storage', 'store']):
            return "Proper rice storage requires: 1) Moisture content below 14%, 2) Clean, dry storage areas, 3) Protection from pests, 4) Good ventilation, 5) Regular monitoring. Use airtight containers for small quantities."
        
        elif any(word in message_lower for word in ['market', 'trend']):
            return "Current market trends show stable demand for premium varieties like Basmati. Organic and brown rice segments are growing. Regional preferences vary - South India prefers Sona Masoori, North India favors Basmati."
        
        else:
            return "I'm here to help with rice trading, market information, and agricultural guidance. You can ask me about prices, quality, storage, market trends, or any other rice-related topics."

def get_market_analysis():
    """Get comprehensive market analysis"""
    try:
        # Get recent market data from database
        market_data = {}
        
        rice_types = ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice']
        
        for rice_type in rice_types:
            # Get recent listings for this rice type
            listings = RiceListing.query.filter_by(
                rice_type=rice_type, 
                is_available=True
            ).all()
            
            if listings:
                prices = [listing.price_per_kg for listing in listings]
                avg_price = sum(prices) / len(prices)
                
                # Determine trend (simplified logic)
                if avg_price > 50:
                    trend = 'increasing'
                elif avg_price < 40:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
                
                # Determine demand level based on number of listings
                if len(listings) > 5:
                    demand_level = 'high'
                elif len(listings) > 2:
                    demand_level = 'medium'
                else:
                    demand_level = 'low'
                
                market_data[rice_type] = {
                    'average_price': round(avg_price, 2),
                    'price_trend': trend,
                    'demand_level': demand_level,
                    'total_listings': len(listings),
                    'total_quantity': sum(listing.quantity for listing in listings),
                    'insights': f"{rice_type} shows {trend} price trend with {demand_level} demand. {len(listings)} active listings available."
                }
            else:
                # Default data if no listings
                market_data[rice_type] = {
                    'average_price': {'Basmati': 65, 'Sona Masoori': 45, 'Ponni': 42, 'Brown Rice': 55}.get(rice_type, 50),
                    'price_trend': 'stable',
                    'demand_level': 'medium',
                    'total_listings': 0,
                    'total_quantity': 0,
                    'insights': f"Limited market data available for {rice_type}. Contact local farmers for current rates."
                }
        
        return market_data
        
    except Exception as e:
        print(f"Error getting market analysis: {e}")
        # Return default analysis
        return {
            'Basmati': {
                'average_price': 65,
                'price_trend': 'stable',
                'demand_level': 'high',
                'insights': 'Premium rice with consistent demand'
            },
            'Sona Masoori': {
                'average_price': 45,
                'price_trend': 'stable',
                'demand_level': 'high',
                'insights': 'Popular in South India with steady market'
            },
            'Brown Rice': {
                'average_price': 55,
                'price_trend': 'increasing',
                'demand_level': 'medium',
                'insights': 'Growing health-conscious market segment'
            }
        }

def get_price_prediction(rice_type, quantity):
    """Get price prediction for rice type and quantity"""
    try:
        # Get current market data
        current_listings = RiceListing.query.filter_by(
            rice_type=rice_type,
            is_available=True
        ).all()
        
        if current_listings:
            current_prices = [listing.price_per_kg for listing in current_listings]
            base_price = sum(current_prices) / len(current_prices)
        else:
            # Default prices if no current data
            default_prices = {
                'Basmati': 65,
                'Sona Masoori': 45,
                'Ponni': 42,
                'Brown Rice': 55
            }
            base_price = default_prices.get(rice_type, 50)
        
        # Apply quantity-based adjustments
        quantity_factor = 1.0
        if quantity > 1000:  # Bulk discount
            quantity_factor = 0.95
        elif quantity > 5000:
            quantity_factor = 0.90
        elif quantity < 50:  # Small quantity premium
            quantity_factor = 1.05
        
        # Add some market volatility (±5%)
        market_factor = random.uniform(0.95, 1.05)
        
        predicted_price = base_price * quantity_factor * market_factor
        
        # Calculate confidence based on available data
        confidence = 0.85 if current_listings else 0.70
        
        return {
            'predicted_price': round(predicted_price, 2),
            'confidence': confidence,
            'factors': {
                'base_price': round(base_price, 2),
                'quantity_adjustment': f"{((quantity_factor - 1) * 100):+.1f}%",
                'market_volatility': f"{((market_factor - 1) * 100):+.1f}%"
            }
        }
        
    except Exception as e:
        print(f"Error predicting price: {e}")
        raise e

def generate_market_insights(rice_type):
    """Generate AI-powered market insights"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Provide current market insights for {rice_type} in India including:
        - Current market conditions
        - Price factors
        - Seasonal trends
        - Regional preferences
        - Quality considerations
        
        Keep the response concise and practical for farmers and buyers.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating market insights: {e}")
        return f"Market analysis for {rice_type}: Stable demand with seasonal price variations. Quality and origin significantly impact pricing."
