from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from routes.analytics import analytics_bp  # Ensure routes/analytics.py exists and defines analytics_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitch_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.register_blueprint(analytics_bp)

if __name__ == '__main__':
    app.run(debug=True)