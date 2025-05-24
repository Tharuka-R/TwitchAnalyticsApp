from flask import Blueprint, render_template, request, redirect, url_for, send_file, make_response, flash
from models import Stream, HourlyStat
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions import db
from datetime import datetime, date
from fpdf import FPDF
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import numpy as np

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
def home():
    streams = Stream.query.order_by(Stream.date.desc()).all()
    return render_template('home.html', streams=streams)

@analytics_bp.route('/clear_streams', methods=['POST'])
def clear_streams():
    HourlyStat.query.delete()
    Stream.query.delete()
    db.session.commit()
    return redirect(url_for('analytics.home'))

@analytics_bp.route('/stream/new', methods=['GET', 'POST'])
def new_stream():
    if request.method == 'POST':
        stream_date = request.form['date']
        title = request.form.get('title', '')
        streamer = request.form.get('streamer', 'Da1lyVitamin')
        stream = Stream(date=datetime.strptime(stream_date, '%Y-%m-%d').date(), title=title, streamer=streamer)
        db.session.add(stream)
        db.session.commit()
        return redirect(url_for('analytics.stream', stream_id=stream.id))
    return render_template('new_stream.html')

@analytics_bp.route('/stream/<int:stream_id>', methods=['GET', 'POST'])
def stream(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    if request.method == 'POST':
        hour = request.form['hour']
        viewers = int(request.form['viewers'])
        followers = int(request.form['followers'])
        # Subs, Donations, Sub Donations, Bit Donations: lists of dicts with username and count/amount
        subs = request.form.getlist('subs_usernames[]')
        donations = request.form.getlist('donations_usernames[]')
        sub_donations = request.form.getlist('sub_donations_usernames[]')
        bit_donations = request.form.getlist('bit_donations_usernames[]')
        bit_amounts = request.form.getlist('bit_donations_amounts[]')
        # Store as JSON string or comma-separated for simplicity
        stat = HourlyStat(
            stream_id=stream.id, hour=hour, viewers=viewers, followers=followers,
            subs=",".join(subs), donations=",".join(donations),
            sub_donations=",".join(sub_donations),
            bit_donations=";".join([f"{u}:{a}" for u, a in zip(bit_donations, bit_amounts)])
        )
        db.session.add(stat)
        db.session.commit()
        return redirect(url_for('analytics.home'))  # Go to home after submit
    stats = HourlyStat.query.filter_by(stream_id=stream.id).order_by(HourlyStat.hour).all()
    # Calculate totals
    total_viewers = sum(s.viewers for s in stats)
    total_followers = sum(s.followers for s in stats)
    # ...add more totals as needed...
    return render_template('stream.html', stream=stream, stats=stats, total_viewers=total_viewers, total_followers=total_followers)

@analytics_bp.route('/reports', methods=['GET', 'POST'])
def reports():
    stats = []
    period = ''
    chart = None
    analysis_text = ""
    if request.method == 'POST':
        period = request.form['period']
        today = date.today()
        if period == 'day':
            stats = HourlyStat.query.filter(HourlyStat.created_at >= today).all()
        elif period == 'week':
            week_ago = today.fromordinal(today.toordinal() - 7)
            stats = HourlyStat.query.filter(HourlyStat.created_at >= week_ago).all()
        elif period == 'month':
            month_ago = today.replace(day=1)
            stats = HourlyStat.query.filter(HourlyStat.created_at >= month_ago).all()
        elif period == 'year':
            year_ago = today.replace(month=1, day=1)
            stats = HourlyStat.query.filter(HourlyStat.created_at >= year_ago).all()
        # Generate chart
        if stats:
            hours = [s.hour for s in stats]
            viewers = [s.viewers for s in stats]
            plt.figure(figsize=(8, 4))
            plt.plot(hours, viewers, marker='o')
            plt.title('Viewers Over Time')
            plt.xlabel('Hour')
            plt.ylabel('Viewers')
            plt.tight_layout()
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            chart = base64.b64encode(img.getvalue()).decode()
            plt.close()
            # Example analysis
            avg_viewers = sum(viewers) / len(viewers)
            analysis_text = f"Average viewers: {avg_viewers:.2f}. " \
                            f"Peak viewers: {max(viewers)} at {hours[viewers.index(max(viewers))]}."
    return render_template('reports.html', stats=stats, period=period, chart=chart, analysis_text=analysis_text)

@analytics_bp.route('/stream/<int:stream_id>/pdf_preview')
def stream_pdf_preview(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    stats = HourlyStat.query.filter_by(stream_id=stream.id).order_by(HourlyStat.hour).all()
    # Generate chart for preview
    chart = None
    if stats:
        hours = [s.hour for s in stats]
        viewers = [s.viewers for s in stats]
        plt.figure(figsize=(8, 4))
        plt.plot(hours, viewers, marker='o')
        plt.title('Viewers Over Time')
        plt.xlabel('Hour')
        plt.ylabel('Viewers')
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart = base64.b64encode(img.getvalue()).decode()
        plt.close()
    return render_template('stream_pdf_preview.html', stream=stream, stats=stats, chart=chart)

@analytics_bp.route('/reports/pdf/<period>')
def reports_pdf(period):
    stats = []
    today = date.today()
    if period == 'day':
        stats = HourlyStat.query.filter(HourlyStat.created_at >= today).all()
    elif period == 'week':
        week_ago = today.fromordinal(today.toordinal() - 7)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= week_ago).all()
    elif period == 'month':
        month_ago = today.replace(day=1)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= month_ago).all()
    elif period == 'year':
        year_ago = today.replace(month=1, day=1)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= year_ago).all()
    # Generate PDF
    pdf = generate_report_pdf(stats, period)
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{period}_report.pdf"'
    return response

@analytics_bp.route('/reports/pdf_preview/<period>')
def reports_pdf_preview(period):
    today = date.today()
    if period == 'day':
        stats = HourlyStat.query.filter(HourlyStat.created_at >= today).all()
    elif period == 'week':
        week_ago = today.fromordinal(today.toordinal() - 7)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= week_ago).all()
    elif period == 'month':
        month_ago = today.replace(day=1)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= month_ago).all()
    elif period == 'year':
        year_ago = today.replace(month=1, day=1)
        stats = HourlyStat.query.filter(HourlyStat.created_at >= year_ago).all()
    else:
        stats = []
    chart_img_bytes = None
    if stats and len(stats) > 0:
        hours = [s.hour for s in stats]
        viewers = [s.viewers for s in stats]
        x = np.arange(len(hours))
        plt.figure(figsize=(8, 4))
        plt.bar(x, viewers, color='#9147ff', alpha=0.7, label='Viewers')
        if len(viewers) > 1:
            z = np.polyfit(x, viewers, 2)
            p = np.poly1d(z)
            plt.plot(x, p(x), color='#00ffe7', linewidth=3, linestyle='-', label='Trend')
        plt.xticks(x, hours, rotation=45)
        plt.title('Viewers Per Hour', fontsize=16, fontweight='bold', color='#9147ff')
        plt.xlabel('Hour', fontsize=12)
        plt.ylabel('Viewers', fontsize=12)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', transparent=True)
        img.seek(0)
        chart_img_bytes = img.getvalue()
        plt.close()
    pdf = generate_report_pdf(stats, period, chart_img_bytes)
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('utf-8')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    response = make_response(pdf_output.read())
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'inline', filename=f'report_{period}_preview.pdf')
    return response

@analytics_bp.route('/stream/<int:stream_id>/pdf_download')
def stream_pdf_download(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    stats = HourlyStat.query.filter_by(stream_id=stream.id).order_by(HourlyStat.hour).all()
    chart_img_bytes = None
    if stats and len(stats) > 0:
        hours = [s.hour for s in stats]
        viewers = [s.viewers for s in stats]
        x = np.arange(len(hours))
        plt.figure(figsize=(8, 4))
        plt.bar(x, viewers, color='#9147ff', alpha=0.7, label='Viewers')
        # Modern smooth trend line
        if len(viewers) > 1:
            z = np.polyfit(x, viewers, 2)
            p = np.poly1d(z)
            plt.plot(x, p(x), color='#00ffe7', linewidth=3, linestyle='-', label='Trend')
        plt.xticks(x, hours, rotation=45)
        plt.title('Viewers Per Hour', fontsize=16, fontweight='bold', color='#9147ff')
        plt.xlabel('Hour', fontsize=12)
        plt.ylabel('Viewers', fontsize=12)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', transparent=True)
        img.seek(0)
        chart_img_bytes = img.getvalue()
        plt.close()
    pdf = generate_report_pdf(stats, "day", chart_img_bytes)
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('utf-8')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return send_file(pdf_output, as_attachment=True, download_name=f'stream_{stream_id}_report.pdf', mimetype='application/pdf')

def generate_report_pdf(stats, period, chart_img_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    # Use Arial for now (closest built-in to Inter for FPDF)
    pdf.set_font("Arial", size=12)
    def safe(val):
        return str(val) if val is not None else "-"
    if stats and len(stats) > 0:
        if period == "day":
            pdf.set_font("Arial", "B", 20)
            pdf.set_text_color(145, 71, 255)
            pdf.cell(0, 15, txt="Daily Twitch Analytics Report", ln=True, align='C')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=12)
            pdf.ln(5)
            hours = [safe(s.hour) for s in stats]
            viewers = [s.viewers for s in stats]
            avg_viewers = sum(viewers) / len(viewers)
            peak_viewers = max(viewers)
            peak_hour = hours[viewers.index(peak_viewers)]
            min_viewers = min(viewers)
            min_hour = hours[viewers.index(min_viewers)]
            std_viewers = np.std(viewers)
            trend = "increasing" if viewers[-1] > viewers[0] else "decreasing" if viewers[-1] < viewers[0] else "stable"
            summary = (
                f"Summary:\n"
                f"- Average viewers: {avg_viewers:.2f}\n"
                f"- Peak viewers: {peak_viewers} at {peak_hour}\n"
                f"- Lowest viewers: {min_viewers} at {min_hour}\n"
                f"- Viewer standard deviation: {std_viewers:.2f}\n"
                f"- Trend: {trend}\n"
            )
            analysis = (
                "Analysis:\n"
                f"- The stream started with {viewers[0]} viewers and ended with {viewers[-1]} viewers.\n"
                f"- The trend for this stream was {trend}.\n"
                f"- Viewer engagement {'increased' if trend == 'increasing' else 'decreased' if trend == 'decreasing' else 'remained stable'} throughout the session.\n"
                f"- Recommendation: Focus on content during peak hours ({peak_hour}) and consider engagement strategies for low periods ({min_hour}).\n"
                f"- Prediction: If current trends continue, next stream may reach a peak of {int(peak_viewers * 1.05)} viewers."
            )
            pdf.multi_cell(0, 10, summary)
            pdf.multi_cell(0, 10, analysis)
            pdf.ln(5)
            if chart_img_bytes:
                chart_path = "chart.png"
                with open(chart_path, "wb") as f:
                    f.write(chart_img_bytes)
                pdf.image(chart_path, x=10, y=pdf.get_y(), w=180)
                pdf.ln(70)
                os.remove(chart_path)
            pdf.set_fill_color(145, 71, 255)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 10)
            headers = ["Hour", "Viewers", "Followers", "Subs", "Donations", "Sub Donos", "Bit Donos"]
            for h in headers:
                pdf.cell(28, 10, h, 1, 0, 'C', 1)
            pdf.ln()
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0, 0, 0)
            for stat in stats:
                pdf.cell(28, 10, safe(stat.hour), 1)
                pdf.cell(28, 10, safe(stat.viewers), 1)
                pdf.cell(28, 10, safe(stat.followers), 1)
                pdf.cell(28, 10, safe(stat.subs), 1)
                pdf.cell(28, 10, safe(stat.donations), 1)
                pdf.cell(28, 10, safe(stat.sub_donations), 1)
                pdf.cell(28, 10, safe(stat.bit_donations), 1)
                pdf.ln()
        # ...existing week/month/year logic unchanged...
    else:
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "No data for this period.", ln=True)
    return pdf
