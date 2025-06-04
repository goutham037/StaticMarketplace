from flask import Blueprint, render_template, request, current_app, session, redirect, url_for, g
from flask_babel import get_locale, refresh, gettext as _

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage with language support"""
    return render_template('main/index.html')

@bp.route('/about')
def about():
    """About page with company information"""
    return render_template('main/about.html')

@bp.route('/contact')
def contact():
    """Contact page with support information"""
    return render_template('main/contact.html')

@bp.route('/help')
def help():
    """Help page with user guides and FAQs"""
    return render_template('main/help.html')

@bp.route('/language/<language>')
def set_language(language):
    """Set user's preferred language"""
    if language in current_app.config['LANGUAGES']:
        session['language'] = language
        session.permanent = True
    return redirect(request.referrer or url_for('main.index'))

@bp.before_request
def before_request():
    """Set global variables before each request"""
    g.locale = str(get_locale())
