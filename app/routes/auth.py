from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext as _
from werkzeug.security import generate_password_hash
from app.models import User
from app import db
import logging

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with location support"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            mobile_number = request.form.get('mobile_number', '').strip()
            location = request.form.get('location', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            user_type = request.form.get('user_type', 'buyer')

            # Validation
            if not all([full_name, mobile_number, location, password, confirm_password]):
                flash(_('All fields are required'), 'error')
                return render_template('auth/register.html')

            if len(mobile_number) != 10 or not mobile_number.isdigit():
                flash(_('Please enter a valid 10-digit mobile number'), 'error')
                return render_template('auth/register.html')

            if password != confirm_password:
                flash(_('Passwords do not match'), 'error')
                return render_template('auth/register.html')

            if len(password) < 8:
                flash(_('Password must be at least 8 characters long'), 'error')
                return render_template('auth/register.html')

            # Check if mobile number already exists
            if User.query.filter_by(mobile_number=mobile_number).first():
                flash(_('Mobile number already registered'), 'error')
                return render_template('auth/register.html')

            # Create new user
            user = User(
                full_name=full_name,
                mobile_number=mobile_number,
                location=location,
                user_type=user_type,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash(_('Registration successful! Please login.'), 'success')
            logging.info(f"New user registered: {full_name} ({mobile_number})")
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash(_('Registration failed. Please try again.'), 'error')

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login authentication"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))

        if not mobile_number or not password:
            flash(_('Please enter both mobile number and password'), 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(mobile_number=mobile_number).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember_me)
            flash(_('Login successful!'), 'success')
            logging.info(f"User logged in: {user.full_name} ({mobile_number})")
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.user_type == 'seller':
                return redirect(url_for('seller.dashboard'))
            else:
                return redirect(url_for('buyer.dashboard'))
        else:
            flash(_('Invalid mobile number or password'), 'error')
            logging.warning(f"Failed login attempt for: {mobile_number}")

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = current_user.full_name
    logout_user()
    flash(_('You have been logged out successfully'), 'success')
    logging.info(f"User logged out: {user_name}")
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)
