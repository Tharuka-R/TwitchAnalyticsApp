from extensions import db
from datetime import datetime

class Stream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    streamer = db.Column(db.String(100), nullable=False)
    hourly_stats = db.relationship('HourlyStat', backref='stream', lazy='dynamic', cascade="all, delete-orphan")

class HourlyStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=False)
    hour = db.Column(db.String(20), nullable=False) # e.g., "10:00", "15:30"
    viewers = db.Column(db.Integer, nullable=False)
    followers = db.Column(db.Integer, nullable=False) # Total followers at this hour
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to specific event types
    subscription_events = db.relationship('SubscriptionEvent', backref='hourly_stat', lazy='dynamic', cascade="all, delete-orphan")
    donation_events = db.relationship('DonationEvent', backref='hourly_stat', lazy='dynamic', cascade="all, delete-orphan")
    bits_donation_events = db.relationship('BitsDonationEvent', backref='hourly_stat', lazy='dynamic', cascade="all, delete-orphan")

# New event tables
class SubscriptionEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hourly_stat_id = db.Column(db.Integer, db.ForeignKey('hourly_stat.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    # tier = db.Column(db.String(50), nullable=True) # Example: "Tier 1", "Prime" - can add later if needed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DonationEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hourly_stat_id = db.Column(db.Integer, db.ForeignKey('hourly_stat.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Assuming currency amount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BitsDonationEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hourly_stat_id = db.Column(db.Integer, db.ForeignKey('hourly_stat.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False) # Number of bits
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
