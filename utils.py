import requests
import math
from typing import Tuple, Optional

def geocode_location(location_text: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a location text to latitude and longitude using OpenStreetMap Nominatim API
    
    Args:
        location_text: Address or location text to geocode
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        # Use Nominatim API for geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_text,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'in'  # Restrict to India
        }
        
        headers = {
            'User-Agent': 'GreenBridge Rice Platform'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        
        return None
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Reverse geocode coordinates to get address
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Address string or None if reverse geocoding fails
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        
        headers = {
            'User-Agent': 'GreenBridge Rice Platform'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', '')
        
        return None
        
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        return None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r

def format_price(price: float) -> str:
    """
    Format price in Indian currency format
    
    Args:
        price: Price value to format
        
    Returns:
        Formatted price string
    """
    return f"₹{price:,.2f}"

def format_quantity(quantity: float, unit: str = 'kg') -> str:
    """
    Format quantity with appropriate unit
    
    Args:
        quantity: Quantity value
        unit: Unit type (kg, quintal, ton)
        
    Returns:
        Formatted quantity string
    """
    if unit == 'quintal' and quantity >= 1000:
        return f"{quantity/100:.1f} quintals"
    elif unit == 'ton' and quantity >= 1000:
        return f"{quantity/1000:.1f} tons"
    else:
        return f"{quantity:.1f} kg"

def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> float:
    """
    Convert quantity between different units
    
    Args:
        quantity: Quantity to convert
        from_unit: Source unit (kg, quintal, ton)
        to_unit: Target unit (kg, quintal, ton)
        
    Returns:
        Converted quantity
    """
    # Convert to kg first
    if from_unit == 'quintal':
        kg_quantity = quantity * 100
    elif from_unit == 'ton':
        kg_quantity = quantity * 1000
    else:
        kg_quantity = quantity
    
    # Convert from kg to target unit
    if to_unit == 'quintal':
        return kg_quantity / 100
    elif to_unit == 'ton':
        return kg_quantity / 1000
    else:
        return kg_quantity

def validate_mobile_number(mobile: str) -> bool:
    """
    Validate Indian mobile number format
    
    Args:
        mobile: Mobile number string
        
    Returns:
        True if valid, False otherwise
    """
    import re
    
    # Remove any spaces or special characters
    mobile = re.sub(r'[^\d]', '', mobile)
    
    # Check if it's a valid Indian mobile number
    # Should be 10 digits starting with 6, 7, 8, or 9
    pattern = r'^[6-9]\d{9}$'
    
    return bool(re.match(pattern, mobile))

def get_rice_type_info(rice_type: str) -> dict:
    """
    Get information about a rice type
    
    Args:
        rice_type: Type of rice
        
    Returns:
        Dictionary with rice information
    """
    rice_info = {
        'Basmati': {
            'description': 'Premium long-grain aromatic rice',
            'characteristics': ['Long grain', 'Aromatic', 'Low starch content'],
            'best_for': ['Biryani', 'Pulav', 'Special occasions'],
            'typical_price_range': '₹60-80 per kg',
            'origin': 'Northern India'
        },
        'Sona Masoori': {
            'description': 'Medium-grain rice popular in South India',
            'characteristics': ['Medium grain', 'Low starch', 'Easy to digest'],
            'best_for': ['Daily meals', 'South Indian dishes'],
            'typical_price_range': '₹40-50 per kg',
            'origin': 'Andhra Pradesh, Karnataka'
        },
        'Ponni': {
            'description': 'Short-grain rice variety from Tamil Nadu',
            'characteristics': ['Short grain', 'High yield', 'Good taste'],
            'best_for': ['South Indian meals', 'Rice dishes'],
            'typical_price_range': '₹40-45 per kg',
            'origin': 'Tamil Nadu'
        },
        'Brown Rice': {
            'description': 'Whole grain rice with high nutritional value',
            'characteristics': ['Whole grain', 'High fiber', 'Nutritious'],
            'best_for': ['Health-conscious consumers', 'Diabetic-friendly meals'],
            'typical_price_range': '₹50-60 per kg',
            'origin': 'Various regions'
        }
    }
    
    return rice_info.get(rice_type, {
        'description': 'Traditional rice variety',
        'characteristics': ['Good quality', 'Versatile'],
        'best_for': ['General cooking'],
        'typical_price_range': 'Varies by region',
        'origin': 'India'
    })
