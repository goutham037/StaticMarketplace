from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from ..models import RiceListing, User, db
from werkzeug.utils import secure_filename
import os

bp = Blueprint('seller', __name__, url_prefix='/seller')

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    listings = RiceListing.query.filter_by(seller_id=user.id).all()
    return render_template('seller/dashboard.html', listings=listings)

@bp.route('/new-listing', methods=['GET', 'POST'])
def new_listing():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        rice_type = request.form.get('rice_type')
        quantity = request.form.get('quantity')
        price_per_kg = request.form.get('price_per_kg')
        image = request.files.get('image')

        if not all([rice_type, quantity, price_per_kg]):
            flash('All fields are required', 'error')
            return render_template('seller/new_listing.html')

        listing = RiceListing(
            seller_id=session['user_id'],
            rice_type=rice_type,
            quantity=float(quantity),
            price_per_kg=float(price_per_kg)
        )

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('app/static/uploads', filename)
            image.save(image_path)
            listing.image_url = f'/static/uploads/{filename}'

        db.session.add(listing)
        db.session.commit()

        flash('Listing created successfully!', 'success')
        return redirect(url_for('seller.dashboard'))

    return render_template('seller/new_listing.html')

@bp.route('/edit-listing/<int:id>', methods=['GET', 'POST'])
def edit_listing(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    listing = RiceListing.query.get_or_404(id)
    if listing.seller_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('seller.dashboard'))

    if request.method == 'POST':
        listing.rice_type = request.form.get('rice_type')
        listing.quantity = float(request.form.get('quantity'))
        listing.price_per_kg = float(request.form.get('price_per_kg'))
        listing.is_available = bool(request.form.get('is_available'))

        image = request.files.get('image')
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('app/static/uploads', filename)
            image.save(image_path)
            listing.image_url = f'/static/uploads/{filename}'

        db.session.commit()
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('seller.dashboard'))

    return render_template('seller/edit_listing.html', listing=listing)

@bp.route('/delete-listing/<int:id>', methods=['POST'])
def delete_listing(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    listing = RiceListing.query.get_or_404(id)
    if listing.seller_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('seller.dashboard'))
    
    # Delete the image file if it exists
    if listing.image_url:
        image_path = os.path.join('app', listing.image_url.lstrip('/'))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('seller.dashboard')) 