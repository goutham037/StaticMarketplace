from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.models import RiceListing, User
from app import db
import logging
from datetime import datetime

bp = Blueprint('seller', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    """Seller dashboard with listings management"""
    listings = RiceListing.query.filter_by(seller_id=current_user.id).order_by(RiceListing.created_at.desc()).all()
    
    # Calculate dashboard statistics
    total_listings = len(listings)
    active_listings = len([l for l in listings if l.is_available])
    total_quantity = sum(l.quantity for l in listings if l.is_available)
    avg_price = sum(l.price_per_kg for l in listings if l.is_available) / max(active_listings, 1)
    
    stats = {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'total_quantity': total_quantity,
        'avg_price': round(avg_price, 2)
    }
    
    return render_template('seller/dashboard.html', listings=listings, stats=stats)

@bp.route('/new-listing', methods=['GET', 'POST'])
@login_required
def new_listing():
    """Create new rice listing"""
    if request.method == 'POST':
        try:
            # Get form data
            rice_type = request.form.get('rice_type', '').strip()
            variety = request.form.get('variety', '').strip()
            quantity = request.form.get('quantity', type=float)
            price_per_kg = request.form.get('price_per_kg', type=float)
            quality_grade = request.form.get('quality_grade', 'A')
            processing_type = request.form.get('processing_type', 'Raw')
            organic = bool(request.form.get('organic'))
            description = request.form.get('description', '').strip()
            minimum_order = request.form.get('minimum_order', type=float) or 10.0
            harvest_date = request.form.get('harvest_date')
            storage_location = request.form.get('storage_location', '').strip()

            # Validation
            if not all([rice_type, quantity, price_per_kg]):
                flash(_('Rice type, quantity, and price are required'), 'error')
                return render_template('seller/new_listing.html')

            if quantity <= 0 or price_per_kg <= 0:
                flash(_('Quantity and price must be positive numbers'), 'error')
                return render_template('seller/new_listing.html')

            # Parse harvest date
            harvest_date_obj = None
            if harvest_date:
                try:
                    harvest_date_obj = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                except ValueError:
                    flash(_('Invalid harvest date format'), 'error')
                    return render_template('seller/new_listing.html')

            # Create new listing
            listing = RiceListing(
                seller_id=current_user.id,
                rice_type=rice_type,
                variety=variety,
                quantity=quantity,
                price_per_kg=price_per_kg,
                quality_grade=quality_grade,
                processing_type=processing_type,
                organic=organic,
                description=description,
                minimum_order=minimum_order,
                harvest_date=harvest_date_obj,
                storage_location=storage_location
            )

            db.session.add(listing)
            db.session.commit()

            flash(_('Listing created successfully!'), 'success')
            logging.info(f"New listing created by {current_user.full_name}: {rice_type} - {quantity}kg")
            return redirect(url_for('seller.dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating listing: {str(e)}")
            flash(_('Failed to create listing. Please try again.'), 'error')

    return render_template('seller/new_listing.html')

@bp.route('/edit-listing/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_listing(id):
    """Edit existing rice listing"""
    listing = RiceListing.query.get_or_404(id)
    
    # Check if current user owns this listing
    if listing.seller_id != current_user.id:
        flash(_('Unauthorized access to this listing'), 'error')
        return redirect(url_for('seller.dashboard'))

    if request.method == 'POST':
        try:
            # Update listing with form data
            listing.rice_type = request.form.get('rice_type', '').strip()
            listing.variety = request.form.get('variety', '').strip()
            listing.quantity = float(request.form.get('quantity', 0))
            listing.price_per_kg = float(request.form.get('price_per_kg', 0))
            listing.quality_grade = request.form.get('quality_grade', 'A')
            listing.processing_type = request.form.get('processing_type', 'Raw')
            listing.organic = bool(request.form.get('organic'))
            listing.description = request.form.get('description', '').strip()
            listing.minimum_order = float(request.form.get('minimum_order', 10.0))
            listing.is_available = bool(request.form.get('is_available'))
            listing.storage_location = request.form.get('storage_location', '').strip()

            # Parse harvest date
            harvest_date = request.form.get('harvest_date')
            if harvest_date:
                try:
                    listing.harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                except ValueError:
                    flash(_('Invalid harvest date format'), 'error')
                    return render_template('seller/edit_listing.html', listing=listing)

            # Validation
            if not all([listing.rice_type, listing.quantity, listing.price_per_kg]):
                flash(_('Rice type, quantity, and price are required'), 'error')
                return render_template('seller/edit_listing.html', listing=listing)

            if listing.quantity <= 0 or listing.price_per_kg <= 0:
                flash(_('Quantity and price must be positive numbers'), 'error')
                return render_template('seller/edit_listing.html', listing=listing)

            db.session.commit()
            flash(_('Listing updated successfully!'), 'success')
            logging.info(f"Listing updated by {current_user.full_name}: ID {id}")
            return redirect(url_for('seller.dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating listing: {str(e)}")
            flash(_('Failed to update listing. Please try again.'), 'error')

    return render_template('seller/edit_listing.html', listing=listing)

@bp.route('/delete-listing/<int:id>', methods=['POST'])
@login_required
def delete_listing(id):
    """Delete rice listing"""
    try:
        listing = RiceListing.query.get_or_404(id)
        
        # Check if current user owns this listing
        if listing.seller_id != current_user.id:
            flash(_('Unauthorized access to this listing'), 'error')
            return redirect(url_for('seller.dashboard'))

        rice_type = listing.rice_type
        quantity = listing.quantity
        
        db.session.delete(listing)
        db.session.commit()
        
        flash(_('Listing deleted successfully!'), 'success')
        logging.info(f"Listing deleted by {current_user.full_name}: {rice_type} - {quantity}kg")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting listing: {str(e)}")
        flash(_('Failed to delete listing. Please try again.'), 'error')
    
    return redirect(url_for('seller.dashboard'))

@bp.route('/api/toggle-availability/<int:id>', methods=['POST'])
@login_required
def toggle_availability(id):
    """Toggle listing availability via API"""
    try:
        listing = RiceListing.query.get_or_404(id)
        
        # Check if current user owns this listing
        if listing.seller_id != current_user.id:
            return jsonify({
                'success': False,
                'error': _('Unauthorized access')
            }), 403

        listing.is_available = not listing.is_available
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_available': listing.is_available,
            'message': _('Listing availability updated successfully!')
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling availability: {str(e)}")
        return jsonify({
            'success': False,
            'error': _('Failed to update availability')
        }), 500
