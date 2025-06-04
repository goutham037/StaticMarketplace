from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.models import RiceListing, User, MarketAnalysis
from app import db
import logging
import math

bp = Blueprint('buyer', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    """Buyer dashboard with location-based search"""
    return render_template('buyer/dashboard.html')

@bp.route('/search')
@login_required
def search():
    """Search rice listings with filters"""
    rice_type = request.args.get('rice_type')
    quality_grade = request.args.get('quality_grade')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    organic_only = request.args.get('organic', type=bool)
    
    # Build query
    query = RiceListing.query.filter_by(is_available=True)
    
    if rice_type:
        query = query.filter_by(rice_type=rice_type)
    if quality_grade:
        query = query.filter_by(quality_grade=quality_grade)
    if min_price:
        query = query.filter(RiceListing.price_per_kg >= min_price)
    if max_price:
        query = query.filter(RiceListing.price_per_kg <= max_price)
    if organic_only:
        query = query.filter_by(organic=True)
    
    listings = query.order_by(RiceListing.created_at.desc()).all()
    
    # Format listings for map display
    map_listings = []
    for listing in listings:
        if listing.seller.latitude and listing.seller.longitude:
            map_listings.append({
                'id': listing.id,
                'position': {
                    'lat': listing.seller.latitude,
                    'lng': listing.seller.longitude
                },
                'title': f'{listing.rice_type} - ₹{listing.price_per_kg}/kg',
                'seller_name': listing.seller.full_name,
                'quantity': listing.quantity,
                'quality_grade': listing.quality_grade
            })
    
    # Get buyer's location for map centering
    buyer_location = None
    if current_user.latitude and current_user.longitude:
        buyer_location = {
            'lat': current_user.latitude,
            'lng': current_user.longitude
        }
    
    return render_template('buyer/search.html',
                         listings=listings,
                         map_listings=map_listings,
                         buyer_location=buyer_location)

@bp.route('/listing/<int:id>')
@login_required
def view_listing(id):
    """View detailed rice listing"""
    listing = RiceListing.query.get_or_404(id)
    seller = listing.seller
    
    # Calculate distance if both locations are available
    distance = None
    if (current_user.latitude and current_user.longitude and 
        seller.latitude and seller.longitude):
        distance = calculate_distance(
            current_user.latitude, current_user.longitude,
            seller.latitude, seller.longitude
        )
    
    return render_template('buyer/view_listing.html', 
                         listing=listing, 
                         seller=seller,
                         distance=distance)

@bp.route('/api/find-farmers', methods=['POST'])
@login_required
def find_farmers():
    """Find nearby farmers based on criteria"""
    try:
        data = request.get_json()
        rice_type = data.get('riceType')
        quantity = float(data.get('quantity', 0))
        unit = data.get('unit', 'kg')
        max_distance = data.get('maxDistance', 50)  # km
        
        # Convert quantity to kg
        if unit == 'quintal':
            quantity *= 100
        elif unit == 'ton':
            quantity *= 1000
        
        # Base query for available listings
        query = RiceListing.query.filter_by(is_available=True)
        
        if rice_type and rice_type != 'any':
            query = query.filter_by(rice_type=rice_type)
        
        # Filter by minimum quantity availability
        query = query.filter(RiceListing.quantity >= quantity)
        
        listings = query.all()
        
        # Calculate distances and filter by location
        farmers = []
        if current_user.latitude and current_user.longitude:
            for listing in listings:
                seller = listing.seller
                if seller.latitude and seller.longitude:
                    distance = calculate_distance(
                        current_user.latitude, current_user.longitude,
                        seller.latitude, seller.longitude
                    )
                    
                    if distance <= max_distance:
                        farmers.append({
                            'id': str(listing.id),
                            'name': seller.full_name,
                            'location': seller.location,
                            'distance': round(distance, 1),
                            'available_quantity': listing.quantity,
                            'price_per_kg': listing.price_per_kg,
                            'quality_grade': listing.quality_grade,
                            'organic': listing.organic,
                            'rice_type': listing.rice_type
                        })
        
        # Sort by distance
        farmers.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'farmers': farmers[:20]  # Limit to top 20 results
        })
        
    except Exception as e:
        logging.error(f"Error finding farmers: {str(e)}")
        return jsonify({
            'success': False,
            'error': _('Error searching for farmers. Please try again.')
        }), 500

@bp.route('/api/contact-farmer/<int:listing_id>', methods=['POST'])
@login_required
def contact_farmer(listing_id):
    """Contact farmer for a specific listing"""
    try:
        listing = RiceListing.query.get_or_404(listing_id)
        data = request.get_json()
        message = data.get('message', '')
        
        # In a real application, this would send a message or notification
        # For demo purposes, we'll just log the contact attempt
        logging.info(f"Contact request from {current_user.full_name} to {listing.seller.full_name} for listing {listing_id}")
        
        return jsonify({
            'success': True,
            'message': _('Your message has been sent to the farmer successfully!')
        })
        
    except Exception as e:
        logging.error(f"Error contacting farmer: {str(e)}")
        return jsonify({
            'success': False,
            'error': _('Failed to send message. Please try again.')
        }), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c
