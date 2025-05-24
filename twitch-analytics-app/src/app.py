import os
from flask import Flask, render_template
from extensions import db

app = Flask(__name__)

# Use environment variables for sensitive config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///twitch_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')  # Change for production

db.init_app(app)

import models  # Import models after db.init_app(app)
from routes.analytics import analytics_bp  # Import blueprints after models

# Register a named route for the homepage so url_for('home') works everywhere
@app.route('/')
def home():
    from models import Stream
    streams = Stream.query.order_by(Stream.date.desc()).all()
    return render_template('home.html', streams=streams)

app.register_blueprint(analytics_bp)  # No url_prefix

# Health check route for production readiness
@app.route('/health')
def health():
    return 'OK', 200

# Custom error handler for user-friendly error messages
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Set debug=False for production
    app.run(debug=True)