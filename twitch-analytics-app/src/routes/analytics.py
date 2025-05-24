from flask import Blueprint, render_template, request, redirect, url_for, send_file, make_response, flash
from models import Stream, HourlyStat, SubscriptionEvent, DonationEvent, BitsDonationEvent # Models are still needed for stream creation
from extensions import db
from datetime import datetime, date # date is used in one route, datetime for stream creation
import io # For send_file
import base64 # For embedding chart images in HTML

# Import services
from services.analysis_service import get_stream_summary, get_periodic_summary
from services.report_service import generate_viewers_chart, generate_single_stream_report_pdf, generate_periodic_report_pdf

# sys.path.append might still be here if not addressed by packaging. For now, assume it is.
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
def home():
    streams = Stream.query.order_by(Stream.date.desc()).all()
    return render_template('home.html', streams=streams)

@analytics_bp.route('/clear_streams', methods=['POST'])
def clear_streams():
    # Cascade delete should handle related events due to model definitions
    SubscriptionEvent.query.delete()
    DonationEvent.query.delete()
    BitsDonationEvent.query.delete()
    HourlyStat.query.delete()
    Stream.query.delete()
    db.session.commit()
    flash('All streams and associated data have been cleared.', 'success')
    return redirect(url_for('analytics.home'))

@analytics_bp.route('/stream/new', methods=['GET', 'POST'])
def new_stream():
    if request.method == 'POST':
        stream_date_str = request.form['date']
        title = request.form.get('title', 'Untitled Stream')
        streamer = request.form.get('streamer')
        
        if not streamer or not streamer.strip():
            flash('Streamer name is required.', 'danger')
            # Pass back other form values to repopulate the form
            return render_template('new_stream.html', title=title, date=stream_date_str, streamer_val=streamer)
        streamer = streamer.strip() # Use the stripped version

        try:
            stream_date = datetime.strptime(stream_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('new_stream.html', title=title, date=stream_date_str, streamer_val=streamer) # Stay on page, pass back values

        stream = Stream(date=stream_date, title=title, streamer=streamer)
        db.session.add(stream)
        db.session.commit()
        flash(f'Stream "{title}" on {stream_date_str} created successfully.', 'success')
        return redirect(url_for('analytics.stream', stream_id=stream.id))
    return render_template('new_stream.html')

@analytics_bp.route('/stream/<int:stream_id>', methods=['GET', 'POST'])
def stream(stream_id):
    # POST request for adding hourly stats and events (already updated in a previous step)
    if request.method == 'POST':
        # This part was updated in Step 3 to use new models and is assumed correct.
        # For brevity, not repeating that large chunk of code here.
        # It should handle form parsing, creating HourlyStat and related Event objects.
        # --- Start of POST section from previous step (condensed) ---
        hour = request.form['hour']
        try:
            viewers = int(request.form['viewers'])
            followers = int(request.form['followers'])
        except ValueError:
            flash('Invalid number for viewers or followers.', 'danger')
            return redirect(url_for('analytics.stream', stream_id=stream_id))

        stat = HourlyStat(stream_id=stream_id, hour=hour, viewers=viewers, followers=followers)
        db.session.add(stat)

        subs_usernames = request.form.getlist('subs_usernames[]')
        for username in subs_usernames:
            if username.strip():
                db.session.add(SubscriptionEvent(hourly_stat=stat, username=username.strip()))
        
        sub_donation_usernames = request.form.getlist('sub_donations_usernames[]')
        for username in sub_donation_usernames:
            if username.strip():
                db.session.add(SubscriptionEvent(hourly_stat=stat, username=username.strip()))

        donation_usernames = request.form.getlist('donations_usernames[]')
        donation_amounts = request.form.getlist('donations_amounts[]')
        for username, amount_str in zip(donation_usernames, donation_amounts):
            if username.strip() and amount_str.strip():
                try:
                    db.session.add(DonationEvent(hourly_stat=stat, username=username.strip(), amount=float(amount_str)))
                except ValueError:
                    flash(f"Invalid amount '{amount_str}' for donation by {username.strip()}. Skipped.", 'warning')
        
        bit_donation_usernames = request.form.getlist('bit_donations_usernames[]')
        bit_amounts = request.form.getlist('bit_donations_amounts[]')
        for username, amount_str in zip(bit_donation_usernames, bit_amounts):
            if username.strip() and amount_str.strip():
                try:
                    db.session.add(BitsDonationEvent(hourly_stat=stat, username=username.strip(), amount=int(amount_str)))
                except ValueError:
                    flash(f"Invalid amount '{amount_str}' for bits by {username.strip()}. Skipped.", 'warning')
        try:
            db.session.commit()
            flash('Hourly data added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving data: {str(e)}', 'danger')
        return redirect(url_for('analytics.stream', stream_id=stream_id))
        # --- End of POST section ---

    # GET request: Display stream details, stats, and chart
    stream_summary = get_stream_summary(stream_id) # From analysis_service
    
    chart_image_bytes = generate_viewers_chart(stream_summary['all_hourly_stats'], 
                                               chart_title=f"Viewers for Stream on {stream_summary['stream'].date.strftime('%Y-%m-%d')}")
    chart_base64 = None
    if chart_image_bytes:
        chart_base64 = base64.b64encode(chart_image_bytes).decode('utf-8')

    # The stream_summary contains 'stream' (Stream object), 'all_hourly_stats', and aggregated data like 'average_viewers', etc.
    return render_template('stream.html', 
                           stream=stream_summary['stream'], 
                           stats=stream_summary['all_hourly_stats'], # For hourly table
                           summary=stream_summary, # For summary display
                           chart_base64=chart_base64)


@analytics_bp.route('/reports', methods=['GET', 'POST'])
def reports():
    period = request.form.get('period', 'day') # Default to 'day' on GET
    periodic_summary = None
    chart_base64 = None
    analysis_text_parts = [] # For constructing some textual summary

    if request.method == 'POST' or period: # Also process for GET if period is in URL (e.g. bookmarked)
        periodic_summary = get_periodic_summary(period) # From analysis_service
        
        if periodic_summary and periodic_summary['aggregated_hourly_stats']:
            # Generate chart for the aggregated hourly stats in the period
            # This chart might need refinement based on how aggregated_hourly_stats are structured
            # For now, it will plot all data points. A more advanced chart might average or sum per hour/day.
            chart_image_bytes = generate_viewers_chart(periodic_summary['aggregated_hourly_stats'], 
                                                       chart_title=f"Viewer Data for {period.capitalize()}")
            if chart_image_bytes:
                chart_base64 = base64.b64encode(chart_image_bytes).decode('utf-8')
        
        if periodic_summary:
            analysis_text_parts.append(f"Period: {periodic_summary['period_name'].capitalize()} (starting {periodic_summary['start_date'].strftime('%Y-%m-%d')})")
            analysis_text_parts.append(f"Streams found: {periodic_summary['stream_count']}")
            analysis_text_parts.append(f"Overall Average Viewers (per stream): {periodic_summary['overall_average_viewers']:.2f}")
            analysis_text_parts.append(f"Highest Peak Viewers: {periodic_summary['total_peak_viewers_overall']}")
            # Add more details as needed

    return render_template('reports.html', 
                           selected_period=period, 
                           summary=periodic_summary, # Pass the whole summary dict
                           chart_base64=chart_base64, 
                           analysis_text=" | ".join(analysis_text_parts))

@analytics_bp.route('/stream/<int:stream_id>/pdf_preview')
def stream_pdf_preview(stream_id):
    stream_summary = get_stream_summary(stream_id)
    chart_bytes = generate_viewers_chart(stream_summary['all_hourly_stats'], 
                                         chart_title=f"Viewers for Stream on {stream_summary['stream'].date.strftime('%Y-%m-%d')}")
    
    pdf_bytes = generate_single_stream_report_pdf(stream_summary, stream_summary['all_hourly_stats'], chart_bytes)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="stream_{stream_id}_preview.pdf"'
    return response

@analytics_bp.route('/stream/<int:stream_id>/pdf_download')
def stream_pdf_download(stream_id):
    stream_summary = get_stream_summary(stream_id)
    chart_bytes = generate_viewers_chart(stream_summary['all_hourly_stats'],
                                         chart_title=f"Viewers for Stream on {stream_summary['stream'].date.strftime('%Y-%m-%d')}")
                                         
    pdf_bytes = generate_single_stream_report_pdf(stream_summary, stream_summary['all_hourly_stats'], chart_bytes)
    
    return send_file(io.BytesIO(pdf_bytes), 
                     as_attachment=True, 
                     download_name=f'stream_{stream_id}_report.pdf', 
                     mimetype='application/pdf')

@analytics_bp.route('/reports/pdf_download/<period>') # For download
def reports_pdf_download(period): # Renamed for clarity from reports_pdf
    periodic_summary = get_periodic_summary(period)
    chart_bytes = None
    if periodic_summary and periodic_summary['aggregated_hourly_stats']:
        chart_bytes = generate_viewers_chart(periodic_summary['aggregated_hourly_stats'], 
                                             chart_title=f"Aggregated Viewer Data - {period.capitalize()}")

    pdf_bytes = generate_periodic_report_pdf(periodic_summary, chart_bytes)
    
    return send_file(io.BytesIO(pdf_bytes), 
                     as_attachment=True, 
                     download_name=f'{period}_report.pdf', 
                     mimetype='application/pdf')


@analytics_bp.route('/reports/pdf_preview/<period>')
def reports_pdf_preview(period):
    periodic_summary = get_periodic_summary(period)
    chart_bytes = None
    if periodic_summary and periodic_summary['aggregated_hourly_stats']:
        chart_bytes = generate_viewers_chart(periodic_summary['aggregated_hourly_stats'],
                                             chart_title=f"Aggregated Viewer Data Preview - {period.capitalize()}")

    pdf_bytes = generate_periodic_report_pdf(periodic_summary, chart_bytes)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="report_{period}_preview.pdf"'
    return response

# The old generate_report_pdf function (long FPDF code) should be entirely removed from this file.
# Also, direct usage of matplotlib (plt) and numpy (np) should be removed from this file.
# The `sys.path.append` at the top might be removed if python path is properly configured.
