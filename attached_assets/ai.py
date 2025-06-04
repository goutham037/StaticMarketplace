from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime, timedelta
from ..models import *
import json
import numpy as np
from collections import defaultdict
import os
import logging

# Import Gemini AI client libraries
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Initialize Gemini client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Set up safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('ai', __name__, url_prefix='/ai')

def call_gemini(prompt: str, max_retries=3) -> str:
    """
    Send a prompt to Gemini AI and return the generated text
    with enhanced error handling and retry logic
    """
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    top_p=0.95,
                    top_k=40
                )
            )
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Gemini API error (attempt {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                print("sss")# Wait before retrying
    
    logger.error("All Gemini attempts failed. Using fallback response")
    return "I'm experiencing technical difficulties. Please try again later."

@bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to use the chatbot'}), 401

    if request.method == 'POST':
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Build context-aware prompt
        context = (
            "You are RICE AI, an expert agricultural assistant specializing in rice cultivation, "
            "market trends, and farming techniques. You're helping farmers, traders, and agricultural "
            "professionals. Provide detailed, practical advice tailored to smallholder farmers in "
            "developing countries. Cover topics like:\n"
            "- Rice varieties and their characteristics\n"
            "- Pest/disease management\n"
            "- Water conservation techniques\n"
            "- Soil health improvement\n"
            "- Harvesting and post-harvest processing\n"
            "- Market prices and trends\n"
            "- Government schemes and subsidies\n"
            "- Climate-smart practices\n\n"
            "Current user question:"
        )
        full_prompt = f"{context}\n\n{message}"

        try:
            response = call_gemini(full_prompt)
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            response = ("I'm having trouble connecting to the knowledge base. "
                        "Please try again shortly. Meanwhile, you might want to "
                        "check the market analysis section for recent trends.")

        # Save the chat message
        chat_message = ChatMessage(
            user_id=session['user_id'],
            message=message,
            response=response
        )
        db.session.add(chat_message)
        db.session.commit()

        return jsonify({
            'response': response,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    # Get chat history for GET requests
    chat_history = ChatMessage.query.filter_by(user_id=session['user_id']).order_by(ChatMessage.created_at.desc()).limit(10).all()
    return render_template('ai/chat.html', chat_history=chat_history)

@bp.route('/market-analysis')
def market_analysis():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to view market analysis'}), 401

    # Get recent listings for analysis
    recent_listings = RiceListing.query.filter(
        RiceListing.created_at >= datetime.now() - timedelta(days=30)
    ).all()

    # Analyze market trends
    analysis = analyze_market_trends(recent_listings)
    
    return render_template('ai/market_analysis.html', analysis=analysis)

@bp.route('/price-prediction', methods=['POST'])
def price_prediction():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to use price prediction'}), 401

    data = request.json
    rice_type = data.get('rice_type')
    quantity = data.get('quantity')
    region = data.get('region', 'national')

    if not all([rice_type, quantity]):
        return jsonify({'error': 'Rice type and quantity are required'}), 400

    # Get historical data for prediction
    historical_data = RiceListing.query.filter_by(rice_type=rice_type).all()
    predicted_price = predict_price(rice_type, float(quantity), historical_data)

    # Generate comprehensive report with Gemini
    insights_prompt = (
        f"Generate a comprehensive rice market report for farmers including:\n"
        f"1. Current {rice_type} price prediction: {predicted_price:.2f}/kg for {quantity}kg\n"
        f"2. Regional analysis ({region} focus)\n"
        f"3. Seasonal trends and projections\n"
        f"4. Farming cost breakdown (seeds, fertilizer, labor)\n"
        f"5. Comparative profitability analysis\n"
        f"6. Storage and transportation advice\n"
        f"7. Government support programs\n"
        f"8. Recommended selling strategies\n\n"
        "Use clear, actionable language suitable for small farmers. "
        "Include concrete numbers where possible and practical recommendations."
    )
    
    try:
        full_report = call_gemini(insights_prompt)
    except Exception as e:
        logger.error(f"Prediction report error: {str(e)}")
        full_report = f"Predicted price: ₹{predicted_price:.2f}/kg for {quantity}kg of {rice_type}. Detailed analysis unavailable."

    return jsonify({
        'predicted_price': predicted_price,
        'full_report': full_report
    })


def analyze_market_trends(listings):
    """Analyze market trends from recent listings and generate AI-driven insights"""
    analysis = defaultdict(dict)
    
    for rice_type in ['Basmati', 'Sona Masoori', 'Ponni', 'Brown Rice', 'Jasmine']:
        type_listings = [l for l in listings if l.rice_type == rice_type]
        if not type_listings:
            continue

        prices = [l.price_per_kg for l in type_listings]
        quantities = [l.quantity for l in type_listings]
        
        avg_price = np.mean(prices) if prices else 0
        price_trend = 'stable'
        if len(prices) > 1:
            if prices[-1] > prices[0]:
                price_trend = 'increasing'
            elif prices[-1] < prices[0]:
                price_trend = 'decreasing'

        # Generate AI insights using Gemini
        prompt = (
            f"Generate farmer-friendly market analysis for {rice_type} rice:\n"
            f"- Current average price: ₹{avg_price:.2f}/kg\n"
            f"- Price trend: {price_trend}\n"
            f"- Total recent transactions: {len(type_listings)}\n\n"
            "Include:\n"
            "1. Practical implications for farmers\n"
            "2. Cost-benefit analysis\n"
            "3. Regional price variations\n"
            "4. Recommended actions\n"
            "5. Market outlook (next 3 months)\n"
            "6. Alternative crop suggestions\n"
            "Format in clear bullet points."
        )
        try:
            insights = call_gemini(prompt)
        except Exception:
            insights = f"{rice_type} market: ₹{avg_price:.2f}/kg ({price_trend} trend). Detailed analysis unavailable."

        analysis[rice_type] = {
            'average_price': round(avg_price, 2),
            'price_trend': price_trend,
            'insights': insights
        }

    return analysis


def predict_price(rice_type, quantity, historical_data):
    """Enhanced price prediction based on historical data and market factors"""
    if not historical_data:
        return 0  # Default price

    # Calculate weighted average with recent bias
    weights = np.linspace(1.0, 0.5, len(historical_data))
    prices = np.array([l.price_per_kg for l in historical_data])
    avg_price = np.average(prices, weights=weights)

    # Apply quantity adjustment
    if quantity > 1000:
        avg_price *= 0.92  # 8% bulk discount
    elif quantity < 100:
        avg_price *= 1.08  # 8% small quantity premium
        
    # Seasonal adjustment (example: +5% during festival seasons)
    if datetime.now().month in [9, 10]:  # Festive season
        avg_price *= 1.05
        
    return round(avg_price, 2)