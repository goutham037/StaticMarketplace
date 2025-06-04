from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash
from ..models import User, db

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        mobile_number = request.form.get('mobile_number')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        if not all([full_name, mobile_number, location, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(mobile_number=mobile_number).first():
            flash('Mobile number already registered', 'error')
            return render_template('auth/register.html')

        user = User(
            full_name=full_name,
            mobile_number=mobile_number,
            location=location,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        password = request.form.get('password')

        user = User.query.filter_by(mobile_number=mobile_number).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        
        flash('Invalid mobile number or password', 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('main.index')) 