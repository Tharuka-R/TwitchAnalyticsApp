# twitch-analytics-app/tests/test_report_service.py
import unittest
from unittest.mock import patch, MagicMock, ANY
import io

# Add src to path to allow imports for testing if tests are run from root
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from flask import Flask
from extensions import db # Though not directly used by report_service, good for consistency if we add db interactions
from models import Stream, HourlyStat # For creating test data
from services.report_service import (
    generate_viewers_chart, 
    generate_single_stream_report_pdf, 
    generate_periodic_report_pdf,
    AnalyticsPDF # Could test helper methods if any complex ones existed
)
from services.analysis_service import get_stream_summary, get_periodic_summary # To get data for PDF functions
from datetime import date, datetime


# Basic Flask app setup for context (primarily for analysis_service to work)
def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Needed for analysis_service
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

class ReportServiceTests(unittest.TestCase):

    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all() # For analysis_service data creation

        # Create some basic data that analysis_service can use
        self.test_stream = Stream(date=date(2023,1,1), title="Test Stream for Report", streamer="Reporter")
        db.session.add(self.test_stream)
        db.session.flush()
        hs1 = HourlyStat(stream_id=self.test_stream.id, hour="10:00", viewers=10, followers=5)
        hs2 = HourlyStat(stream_id=self.test_stream.id, hour="11:00", viewers=20, followers=10)
        db.session.add_all([hs1, hs2])
        db.session.commit()

        self.hourly_stats_data = [hs1, hs2]


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('services.report_service.plt') # Mock matplotlib.pyplot
    def test_generate_viewers_chart_with_data(self, mock_plt):
        # Configure mocks for plt figure, savefig, close
        mock_figure = MagicMock()
        mock_plt.figure.return_value = mock_figure
        mock_plt.savefig = MagicMock()
        mock_plt.close = MagicMock()

        chart_bytes = generate_viewers_chart(self.hourly_stats_data, "Test Chart")

        self.assertIsNotNone(chart_bytes)
        self.assertIsInstance(chart_bytes, bytes)
        mock_plt.figure.assert_called_once()
        # Get the actual BytesIO object passed to savefig
        # The first argument of the first call to savefig
        # savefig_args = mock_plt.savefig.call_args[0]
        # self.assertIsInstance(savefig_args[0], io.BytesIO)
        mock_plt.savefig.assert_called_with(ANY, format='png', transparent=True) # ANY for BytesIO
        mock_plt.close.assert_called_once()


    def test_generate_viewers_chart_no_data(self):
        chart_bytes = generate_viewers_chart([], "Empty Test Chart")
        self.assertIsNone(chart_bytes)

    @patch('services.report_service.FPDF') # Mock FPDF base class
    def test_generate_single_stream_report_pdf(self, mock_fpdf_class):
        # Configure the mock for FPDF
        mock_pdf_instance = MagicMock()
        mock_pdf_instance.output.return_value = b"pdf_content_mock" # byte string
        mock_fpdf_class.return_value = mock_pdf_instance
        
        stream_summary = get_stream_summary(self.test_stream.id)
        # Chart bytes can be None or actual bytes from the chart function (mocked separately if needed)
        chart_bytes_dummy = b"dummy_chart_bytes"

        pdf_bytes = generate_single_stream_report_pdf(stream_summary, self.hourly_stats_data, chart_bytes_dummy)

        self.assertEqual(pdf_bytes, b"pdf_content_mock")
        mock_fpdf_class.assert_called_once() # AnalyticsPDF is a subclass, check if FPDF was init
        mock_pdf_instance.add_page.assert_called()
        mock_pdf_instance.output.assert_called_with(dest='S')
        # We could add more assertions on calls to cell, set_font etc. if needed

    @patch('services.report_service.FPDF')
    def test_generate_periodic_report_pdf(self, mock_fpdf_class):
        mock_pdf_instance = MagicMock()
        mock_pdf_instance.output.return_value = b"periodic_pdf_mock"
        mock_fpdf_class.return_value = mock_pdf_instance

        periodic_summary = get_periodic_summary('day') # Uses data created in setUp
        chart_bytes_dummy = b"dummy_chart_bytes"

        pdf_bytes = generate_periodic_report_pdf(periodic_summary, chart_bytes_dummy)
        
        self.assertEqual(pdf_bytes, b"periodic_pdf_mock")
        mock_fpdf_class.assert_called_once()
        mock_pdf_instance.add_page.assert_called()
        mock_pdf_instance.output.assert_called_with(dest='S')


if __name__ == '__main__':
    unittest.main()
