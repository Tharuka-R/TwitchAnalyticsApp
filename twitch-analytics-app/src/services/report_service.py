# twitch-analytics-app/src/services/report_service.py
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Ensure backend is set before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import os # Only for font path if needed, try to avoid direct file system ops for images
from datetime import date

# Helper to safely get string value
def safe_str(val, default="N/A"):
    return str(val) if val is not None else default

def generate_viewers_chart(hourly_stats, chart_title="Viewers Over Time"):
    """
    Generates a line chart for viewers over time from HourlyStat objects.
    Returns PNG image bytes.
    """
    if not hourly_stats:
        return None

    hours = [safe_str(s.hour, "") for s in hourly_stats] # Use safe_str for hour
    viewers = [s.viewers if s.viewers is not None else 0 for s in hourly_stats] # Default to 0 if None

    if not any(viewers): # If all viewers are 0 or stats are empty after processing
        return None

    plt.figure(figsize=(10, 5)) # Adjusted size for better readability
    
    x_ticks = np.arange(len(hours)) # Use numerical ticks for x-axis

    plt.plot(x_ticks, viewers, marker='o', linestyle='-', color='#9147ff', label='Viewers')

    # Trend line if there are enough data points
    if len(viewers) > 1:
        try:
            z = np.polyfit(x_ticks, viewers, min(len(viewers) - 1, 2)) # Degree 2 or 1 if only 2 points
            p = np.poly1d(z)
            plt.plot(x_ticks, p(x_ticks), color='#00ffe7', linewidth=2, linestyle='--', label='Trend')
        except np.RankWarning:
            pass # Ignore RankWarning if polyfit is ill-conditioned
        except Exception: # Catch other potential errors during polyfit
            pass


    plt.title(chart_title, fontsize=16, fontweight='bold', color='#9147ff')
    plt.xlabel('Hour of Stream', fontsize=12)
    plt.ylabel('Concurrent Viewers', fontsize=12)
    plt.xticks(x_ticks, hours, rotation=45, ha="right") # Set string labels for x-ticks
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout() # Adjust layout to prevent labels from being cut off

    img_bytes_io = io.BytesIO()
    plt.savefig(img_bytes_io, format='png', transparent=True)
    plt.close() # Close the plot to free memory
    img_bytes_io.seek(0)
    return img_bytes_io.getvalue()

class AnalyticsPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_margins(15, 15, 15) # Left, Top, Right
        self.set_auto_page_break(True, margin=15) # Bottom margin

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(145, 71, 255) # Twitch Purple
        self.cell(0, 10, 'Twitch Analytics Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(230, 230, 250) # Light lavender
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.ln(4)

    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(145, 71, 255)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Arial', '', 10)
        self.set_text_color(0,0,0)
        self.multi_cell(0, 6, text)
        self.ln()

    def key_value_pair(self, key, value):
        self.set_font('Arial', 'B', 10)
        self.cell(50, 6, key + ":", 0, 0, 'L')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, safe_str(value)) # Use multi_cell for value in case it's long
        # self.ln(1) # Add a small space

    def table_header(self, headers, col_widths):
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(145, 71, 255) # Twitch Purple
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, 'C', 1)
        self.ln()

    def table_row(self, data, col_widths, is_odd_row):
        self.set_font('Arial', '', 8)
        self.set_text_color(0,0,0)
        fill_color_val = 240 if is_odd_row else 255 # Alternate row colors
        self.set_fill_color(fill_color_val, fill_color_val, fill_color_val)
        for i, datum in enumerate(data):
            self.cell(col_widths[i], 6, safe_str(datum), 1, 0, 'L', 1) # Left align data
        self.ln()

def generate_single_stream_report_pdf(stream_summary, hourly_stats_data, chart_image_bytes=None):
    """
    Generates a PDF report for a single stream.
    stream_summary: Dictionary from analysis_service.get_stream_summary
    hourly_stats_data: List of HourlyStat objects for the stream
    chart_image_bytes: PNG image bytes for the viewers chart
    Returns PDF bytes.
    """
    pdf = AnalyticsPDF()
    pdf.add_page()
    
    stream = stream_summary['stream']
    pdf.chapter_title(f"Stream Report: {safe_str(stream.title, 'Untitled Stream')}")
    pdf.key_value_pair("Stream Date", safe_str(stream.date.strftime('%Y-%m-%d') if stream.date else 'N/A'))
    pdf.key_value_pair("Streamer", safe_str(stream.streamer))
    pdf.ln(5)

    pdf.section_title("Overall Performance")
    pdf.key_value_pair("Average Viewers", f"{stream_summary['average_viewers']:.2f}")
    pdf.key_value_pair("Peak Viewers", safe_str(stream_summary['peak_viewers']))
    pdf.key_value_pair("Total Subscriptions", safe_str(stream_summary['total_subscriptions']))
    pdf.key_value_pair("Total Donation Amount", f"${stream_summary['total_donation_amount']:.2f}")
    pdf.key_value_pair("Total Bits Amount", safe_str(stream_summary['total_bits_amount']))
    pdf.key_value_pair("Followers Gained (Approx.)", safe_str(stream_summary['followers_gained_approx']))
    pdf.ln(5)

    if chart_image_bytes:
        pdf.section_title("Viewers Over Time")
        try:
            # FPDF's image function needs a path or a file-like object.
            # If it's in memory, we give it a name.
            pdf.image(io.BytesIO(chart_image_bytes), x=pdf.get_x(), w=pdf.w - pdf.l_margin - pdf.r_margin, type='PNG')
            pdf.ln(2) # Space after image
        except Exception as e:
            pdf.body_text(f"Error embedding chart: {str(e)}")
    
    pdf.ln(5)
    pdf.section_title("Hourly Breakdown")
    if hourly_stats_data:
        headers = ["Hour", "Viewers", "Followers"] # Simplified, add events later if needed
        # Calculate dynamic widths, ensure sum is page_width - margins
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [page_width * 0.2, page_width * 0.2, page_width * 0.2] # Example widths
        # Add more columns for events if required:
        # headers.extend(["New Subs", "New Donations", "New Bits"])
        # col_widths.extend([page_width * 0.1, page_width * 0.15, page_width * 0.15])


        pdf.table_header(headers, col_widths)
        for i, stat in enumerate(hourly_stats_data):
            # For a single stream report, you might want to list counts of events per hour
            # subs_this_hour = stat.subscription_events.count()
            # donations_this_hour = stat.donation_events.count()
            # bits_this_hour = stat.bits_donation_events.count()
            # data_row = [stat.hour, stat.viewers, stat.followers, subs_this_hour, donations_this_hour, bits_this_hour]
            data_row = [stat.hour, stat.viewers, stat.followers]
            pdf.table_row(data_row, col_widths, is_odd_row=(i % 2 == 0))
    else:
        pdf.body_text("No hourly data available for this stream.")

    pdf_output_bytes = pdf.output(dest='S').encode('latin1') # Use latin1 for FPDF default
    return pdf_output_bytes

def generate_periodic_report_pdf(periodic_summary, chart_image_bytes=None):
    """
    Generates a PDF report for a given period (day, week, month, year).
    periodic_summary: Dictionary from analysis_service.get_periodic_summary
    chart_image_bytes: Optional PNG image bytes for an aggregated chart.
    Returns PDF bytes.
    """
    pdf = AnalyticsPDF()
    pdf.add_page()

    period_name = periodic_summary['period_name'].capitalize()
    start_date_str = periodic_summary['start_date'].strftime('%Y-%m-%d')
    pdf.chapter_title(f"{period_name} Analytics Report (Starting {start_date_str})")
    
    pdf.section_title("Aggregated Performance")
    pdf.key_value_pair("Number of Streams", safe_str(periodic_summary['stream_count']))
    pdf.key_value_pair("Overall Average Viewers (per stream)", f"{periodic_summary['overall_average_viewers']:.2f}")
    pdf.key_value_pair("Highest Peak Viewers", safe_str(periodic_summary['total_peak_viewers_overall']))
    pdf.key_value_pair("Total Subscriptions in Period", safe_str(periodic_summary['total_subscriptions_period']))
    pdf.key_value_pair("Total Donation Amount in Period", f"${periodic_summary['total_donations_period']:.2f}")
    pdf.key_value_pair("Total Bits Amount in Period", safe_str(periodic_summary['total_bits_period']))
    pdf.ln(5)

    if chart_image_bytes: # This chart should represent aggregated data for the period
        pdf.section_title("Viewership Trends (Aggregated)")
        try:
            pdf.image(io.BytesIO(chart_image_bytes), x=pdf.get_x(), w=pdf.w - pdf.l_margin - pdf.r_margin, type='PNG')
            pdf.ln(2)
        except Exception as e:
            pdf.body_text(f"Error embedding aggregated chart: {str(e)}")
    
    pdf.ln(5)
    pdf.section_title("Stream Details")
    if periodic_summary['streams_in_period']:
        headers = ["Date", "Title", "Avg. Viewers", "Peak Viewers", "Subs"]
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [page_width * 0.15, page_width * 0.35, page_width * 0.15, page_width * 0.15, page_width * 0.1]
        
        pdf.table_header(headers, col_widths)
        from services.analysis_service import get_stream_summary # Temporary import for convenience
        
        for i, stream in enumerate(periodic_summary['streams_in_period']):
            # Fetch summary for each stream to display its specific stats
            # This could be optimized if summary data is pre-fetched or simplified
            # For now, this makes the periodic report more detailed.
            # Consider passing simpler pre-calculated stats to avoid N+1 queries here.
            # For this example, let's display data directly available on Stream or from a light query.
            
            # Simplified data for the table row:
            s_date = safe_str(stream.date.strftime('%Y-%m-%d') if stream.date else 'N/A')
            s_title = safe_str(stream.title, 'Untitled')
            
            # These would ideally come from pre-calculated values in periodic_summary if too slow
            # For now, let's get them directly or use placeholders
            hourly_stats_for_this_stream = stream.hourly_stats.all()
            s_avg_viewers = "N/A"
            s_peak_viewers = "N/A"
            if hourly_stats_for_this_stream:
                viewers_list = [hs.viewers for hs in hourly_stats_for_this_stream if hs.viewers is not None]
                if viewers_list:
                    s_avg_viewers = f"{sum(viewers_list)/len(viewers_list):.1f}"
                    s_peak_viewers = str(max(viewers_list))

            s_subs = str(stream.hourly_stats.join(SubscriptionEvent).count()) # Count subs for this stream

            data_row = [s_date, s_title, s_avg_viewers, s_peak_viewers, s_subs]
            pdf.table_row(data_row, col_widths, is_odd_row=(i % 2 == 0))
    else:
        pdf.body_text("No streams found for this period.")

    pdf_output_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_output_bytes
