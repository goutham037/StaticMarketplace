from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from ..models import RiceListing, User
import requests
from flask_login import login_required
from .. import db
import math

bp = Blueprint('buyer', __name__, url_prefix='/buyer')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('buyer/dashboard.html')

@bp.route('/search')
def search():
    rice_type = request.args.get('rice_type')
    listings = RiceListing.query.filter_by(
        rice_type=rice_type,
        is_available=True
    ).all() if rice_type else RiceListing.query.filter_by(is_available=True).all()

    # Get buyer's location
    buyer = User.query.get(session.get('user_id'))
    buyer_location = None
    if buyer and buyer.latitude and buyer.longitude:
        buyer_location = {
            'lat': buyer.latitude,
            'lng': buyer.longitude
        }

    # Format listings for map display
    map_listings = []
    for listing in listings:
        seller = User.query.get(listing.seller_id)
        if seller.latitude and seller.longitude:
            map_listings.append({
                'id': listing.id,
                'position': {
                    'lat': seller.latitude,
                    'lng': seller.longitude
                },
                'title': f'{listing.rice_type} - ₹{listing.price_per_kg}/kg',
                'seller_name': seller.full_name,
                'quantity': listing.quantity
            })

    return render_template('buyer/search.html',
                         listings=listings,
                         map_listings=map_listings,
                         buyer_location=buyer_location)

@bp.route('/listing/<int:id>')
def view_listing(id):
    listing = RiceListing.query.get_or_404(id)
    seller = User.query.get(listing.seller_id)
    return render_template('buyer/view_listing.html', listing=listing, seller=seller)

@bp.route('/nearby-mills')
def nearby_mills():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = User.query.get(session['user_id'])
    if not user.latitude or not user.longitude:
        return jsonify({'error': 'Location not set'}), 400

    # Use Overpass API to find nearby rice mills
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:25];
    (
        node["industrial"="rice_mill"](around:5000,{user.latitude},{user.longitude});
        way["industrial"="rice_mill"](around:5000,{user.latitude},{user.longitude});
        relation["industrial"="rice_mill"](around:5000,{user.latitude},{user.longitude});
    );
    out body;
    >;
    out skel qt;
    """
    
    try:
        response = requests.post(overpass_url, data=overpass_query)
        data = response.json()
        
        mills = []
        for element in data.get('elements', []):
            if element.get('type') == 'node':
                mills.append({
                    'name': element.get('tags', {}).get('name', 'Rice Mill'),
                    'location': {
                        'lat': element.get('lat'),
                        'lng': element.get('lon')
                    },
                    'address': element.get('tags', {}).get('addr:full', 'Address not available')
                })
        
        return jsonify(mills)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/find-farmers', methods=['POST'])
@login_required
def find_farmers():
    data = request.get_json()
    rice_type = data.get('riceType')
    quantity = float(data.get('quantity', 0))
    unit = data.get('unit')
    location = data.get('location')
    
    # Convert all quantities to kg for comparison
    if unit == 'quintal':
        quantity *= 100
    elif unit == 'ton':
        quantity *= 1000

    # TODO: Implement actual farmer search based on location
    # For now, return dummy data
    sample_farmers = [
        {
            'id': '1',
            'name': 'Ramesh Kumar',
            'location': 'Warangal, Telangana',
            'distance': 5.2,
            'available_quantity': 1000,
            'price_per_kg': 45
        },
        {
            'id': '2',
            'name': 'Suresh Reddy',
            'location': 'Karimnagar, Telangana',
            'distance': 8.7,
            'available_quantity': 2000,
            'price_per_kg': 42
        },
        {
            'id': '3',
            'name': 'Venkat Rao',
            'location': 'Nizamabad, Telangana',
            'distance': 12.3,
            'available_quantity': 5000,
            'price_per_kg': 40
        }
    ]

    # Filter farmers based on available quantity
    available_farmers = [
        farmer for farmer in sample_farmers
        if farmer['available_quantity'] >= quantity
    ]

    # Sort by distance
    available_farmers.sort(key=lambda x: x['distance'])

    return jsonify({
        'farmers': available_farmers
    })

@bp.route('/api/contact-farmer/<farmer_id>', methods=['POST'])
@login_required
def contact_farmer(farmer_id):
    # TODO: Implement actual farmer contact logic
    return jsonify({
        'success': True,
        'message': 'Contact request sent to farmer'
    }) 