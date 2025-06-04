from flask import Blueprint, render_template, request, current_app, session, redirect, url_for, g
from flask_babel import get_locale, refresh

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    languages = current_app.config['LANGUAGES']
    return render_template('main/index.html', languages=languages)

@bp.route('/about')
def about():
    languages = current_app.config['LANGUAGES']
    return render_template('main/about.html', languages=languages)

@bp.route('/contact')
def contact():
    languages = current_app.config['LANGUAGES']
    return render_template('main/contact.html', languages=languages)

@bp.route('/help')
def help():
    languages = current_app.config['LANGUAGES']
    return render_template('main/help.html', languages=languages)

@bp.route('/language/<language>')
def set_language(language):
    if language in current_app.config['LANGUAGES']:
        session['language'] = language
    return redirect(request.referrer or url_for('main.index'))

@bp.before_request
def before_request():
    g.locale = str(get_locale()) 