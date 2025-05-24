from extensions import db
from datetime import datetime

class Stream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    streamer = db.Column(db.String(100), nullable=False, default="Da1lyVitamin")
    hourly_stats = db.relationship('HourlyStat', backref='stream', lazy=True)

class HourlyStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=False)
    hour = db.Column(db.String(20), nullable=False)
    viewers = db.Column(db.Integer, nullable=False)
    followers = db.Column(db.Integer, nullable=False)
    subs = db.Column(db.Text, nullable=True)  # Store usernames as comma-separated
    donations = db.Column(db.Text, nullable=True)
    sub_donations = db.Column(db.Text, nullable=True)
    bit_donations = db.Column(db.Text, nullable=True)  # username:amount;username:amount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
