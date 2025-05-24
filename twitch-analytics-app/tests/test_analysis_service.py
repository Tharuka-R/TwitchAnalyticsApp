# twitch-analytics-app/tests/test_analysis_service.py
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src to path to allow imports for testing if tests are run from root
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from flask import Flask
from extensions import db
from models import Stream, HourlyStat, SubscriptionEvent, DonationEvent, BitsDonationEvent
from services.analysis_service import get_stream_summary, get_periodic_summary

# Basic Flask app setup for context
def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

class AnalysisServiceTests(unittest.TestCase):

    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_stream_summary_no_stats(self):
        stream = Stream(date=date(2023, 1, 1), title="Test Stream", streamer="TestUser")
        db.session.add(stream)
        db.session.commit()

        summary = get_stream_summary(stream.id)
        self.assertEqual(summary['stream'].id, stream.id)
        self.assertEqual(summary['total_viewers'], 0)
        self.assertEqual(summary['average_viewers'], 0)
        self.assertEqual(summary['peak_viewers'], 0)
        self.assertEqual(summary['total_subscriptions'], 0)
        self.assertEqual(summary['total_donation_amount'], 0)
        self.assertEqual(summary['total_bits_amount'], 0)
        self.assertEqual(summary['hourly_data_points'], 0)

    def test_get_stream_summary_with_data(self):
        stream = Stream(date=date(2023, 1, 1), title="Gaming Day", streamer="TestUser")
        db.session.add(stream)
        db.session.flush() # Get stream.id

        hs1 = HourlyStat(stream_id=stream.id, hour="10:00", viewers=100, followers=50)
        hs2 = HourlyStat(stream_id=stream.id, hour="11:00", viewers=150, followers=52)
        hs3 = HourlyStat(stream_id=stream.id, hour="12:00", viewers=120, followers=55)
        db.session.add_all([hs1, hs2, hs3])
        db.session.flush() # Get hourly_stat ids

        # Add events
        sub1 = SubscriptionEvent(hourly_stat_id=hs1.id, username="userA")
        sub2 = SubscriptionEvent(hourly_stat_id=hs2.id, username="userB")
        don1 = DonationEvent(hourly_stat_id=hs2.id, username="userC", amount=5.00)
        bits1 = BitsDonationEvent(hourly_stat_id=hs3.id, username="userD", amount=100)
        db.session.add_all([sub1, sub2, don1, bits1])
        db.session.commit()

        summary = get_stream_summary(stream.id)
        
        self.assertEqual(summary['stream'].id, stream.id)
        self.assertEqual(summary['average_viewers'], (100 + 150 + 120) / 3)
        self.assertEqual(summary['peak_viewers'], 150)
        self.assertEqual(summary['total_subscriptions'], 2)
        self.assertEqual(summary['total_donation_amount'], 5.00)
        self.assertEqual(summary['total_bits_amount'], 100)
        self.assertEqual(summary['hourly_data_points'], 3)
        self.assertEqual(summary['first_stat_followers'], 50)
        self.assertEqual(summary['last_stat_followers'], 55)
        self.assertEqual(summary['followers_gained_approx'], 5)

    def test_get_periodic_summary_no_streams(self):
        summary = get_periodic_summary('day')
        self.assertEqual(summary['stream_count'], 0)
        self.assertEqual(summary['total_subscriptions_period'], 0)
        self.assertEqual(summary['overall_average_viewers'], 0)

    def test_get_periodic_summary_with_streams_day(self):
        # Stream 1 today
        s1 = Stream(date=date.today(), title="Today Stream 1", streamer="User1")
        db.session.add(s1)
        db.session.flush()
        hs1_s1 = HourlyStat(stream_id=s1.id, hour="10:00", viewers=50, followers=10)
        db.session.add(hs1_s1)
        db.session.flush()
        db.session.add(SubscriptionEvent(hourly_stat_id=hs1_s1.id, username="subber1"))

        # Stream 2 today
        s2 = Stream(date=date.today(), title="Today Stream 2", streamer="User1")
        db.session.add(s2)
        db.session.flush()
        hs1_s2 = HourlyStat(stream_id=s2.id, hour="14:00", viewers=100, followers=20) # Peak for period
        db.session.add(hs1_s2)
        db.session.flush()
        db.session.add(DonationEvent(hourly_stat_id=hs1_s2.id, username="donator1", amount=10))

        # Stream from yesterday (should not be included in 'day' period)
        s3 = Stream(date=date.today() - timedelta(days=1), title="Yesterday Stream", streamer="User1")
        db.session.add(s3)
        db.session.flush()
        hs1_s3 = HourlyStat(stream_id=s3.id, hour="12:00", viewers=200, followers=5)
        db.session.add(hs1_s3)
        
        db.session.commit()

        summary = get_periodic_summary('day')
        self.assertEqual(summary['period_name'], 'day')
        self.assertEqual(summary['start_date'], date.today())
        self.assertEqual(summary['stream_count'], 2)
        self.assertEqual(summary['total_subscriptions_period'], 1)
        self.assertEqual(summary['total_donations_period'], 10.0)
        self.assertEqual(summary['total_peak_viewers_overall'], 100) # Peak from s2
         # Avg viewers: s1_avg = 50, s2_avg = 100. Overall = (50+100)/2 = 75
        self.assertAlmostEqual(summary['overall_average_viewers'], 75.0)
        self.assertEqual(len(summary['aggregated_hourly_stats']), 2) # hs1_s1, hs1_s2


if __name__ == '__main__':
    unittest.main()
