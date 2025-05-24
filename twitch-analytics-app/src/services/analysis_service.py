# twitch-analytics-app/src/services/analysis_service.py
from models import Stream, HourlyStat, SubscriptionEvent, DonationEvent, BitsDonationEvent
from sqlalchemy import func, desc
from extensions import db
from datetime import date, timedelta

def get_stream_summary(stream_id):
    """
    Calculates summary statistics for a given stream.
    """
    stream = Stream.query.get_or_404(stream_id)
    
    total_viewers = 0
    peak_viewers = 0
    total_followers_gained_during_stream = 0 # This requires a baseline or more complex logic
    
    # Simplified follower calculation: assumes followers count in HourlyStat is cumulative for the stream
    # Or, it's the net followers at that hour. For 'followers gained', we'd need first and last.
    first_stat_followers = None
    last_stat_followers = 0

    hourly_stats_query = stream.hourly_stats.order_by(HourlyStat.hour)
    all_hourly_stats = hourly_stats_query.all()

    if not all_hourly_stats:
        return {
            "stream": stream,
            "total_viewers": 0,
            "average_viewers": 0,
            "peak_viewers": 0,
            "total_subscriptions": 0,
            "total_donation_amount": 0,
            "total_bits_amount": 0,
            "hourly_data_points": 0,
            "first_stat_followers": 0,
            "last_stat_followers": 0,
            "followers_gained_approx": 0,
            "all_hourly_stats": []
        }

    for stat in all_hourly_stats:
        total_viewers += stat.viewers
        if stat.viewers > peak_viewers:
            peak_viewers = stat.viewers
        if first_stat_followers is None:
            first_stat_followers = stat.followers
        last_stat_followers = stat.followers

    average_viewers = total_viewers / len(all_hourly_stats) if all_hourly_stats else 0
    followers_gained_approx = last_stat_followers - (first_stat_followers if first_stat_followers is not None else 0)

    total_subscriptions = db.session.query(func.count(SubscriptionEvent.id)).join(HourlyStat).filter(HourlyStat.stream_id == stream_id).scalar()
    total_donation_amount = db.session.query(func.sum(DonationEvent.amount)).join(HourlyStat).filter(HourlyStat.stream_id == stream_id).scalar() or 0.0
    total_bits_amount = db.session.query(func.sum(BitsDonationEvent.amount)).join(HourlyStat).filter(HourlyStat.stream_id == stream_id).scalar() or 0

    return {
        "stream": stream,
        "total_viewers": total_viewers, # Sum of viewers across all hours (might be less useful than avg)
        "average_viewers": average_viewers,
        "peak_viewers": peak_viewers,
        "total_subscriptions": total_subscriptions,
        "total_donation_amount": total_donation_amount,
        "total_bits_amount": total_bits_amount,
        "hourly_data_points": len(all_hourly_stats),
        "first_stat_followers": first_stat_followers if first_stat_followers is not None else 0,
        "last_stat_followers": last_stat_followers,
        "followers_gained_approx": followers_gained_approx,
        "all_hourly_stats": all_hourly_stats # Pass this for detailed display if needed
    }

def get_periodic_summary(period_name):
    """
    Calculates summary statistics for a given period (day, week, month, year).
    Filters streams based on their date.
    """
    today = date.today()
    start_date = None

    if period_name == 'day':
        start_date = today
    elif period_name == 'week':
        start_date = today - timedelta(days=today.weekday()) # Start of current week (Monday)
    elif period_name == 'month':
        start_date = today.replace(day=1) # Start of current month
    elif period_name == 'year':
        start_date = today.replace(month=1, day=1) # Start of current year
    else: # Default to today if period is unknown
        start_date = today
        period_name = 'day'

    # Query streams within the period
    streams_in_period = Stream.query.filter(Stream.date >= start_date).order_by(desc(Stream.date)).all()

    aggregated_hourly_stats = []
    total_subscriptions_period = 0
    total_donations_period = 0.0
    total_bits_period = 0
    total_average_viewers_sum = 0 # to calculate avg of avgs
    total_peak_viewers_overall = 0
    stream_count = len(streams_in_period)

    for stream_item in streams_in_period:
        # Collect all hourly stats for reports
        # We might want to query HourlyStat directly linked to these streams
        hourly_stats_for_stream = HourlyStat.query.filter(HourlyStat.stream_id == stream_item.id).all()
        aggregated_hourly_stats.extend(hourly_stats_for_stream)
        
        # Sum up events for each stream
        total_subscriptions_period += db.session.query(func.count(SubscriptionEvent.id)).join(HourlyStat).filter(HourlyStat.stream_id == stream_item.id).scalar()
        total_donations_period += db.session.query(func.sum(DonationEvent.amount)).join(HourlyStat).filter(HourlyStat.stream_id == stream_item.id).scalar() or 0.0
        total_bits_period += db.session.query(func.sum(BitsDonationEvent.amount)).join(HourlyStat).filter(HourlyStat.stream_id == stream_item.id).scalar() or 0

        # Viewer stats
        stream_viewers = [hs.viewers for hs in hourly_stats_for_stream if hs.viewers is not None]
        if stream_viewers:
            total_average_viewers_sum += sum(stream_viewers) / len(stream_viewers)
            current_peak = max(stream_viewers)
            if current_peak > total_peak_viewers_overall:
                total_peak_viewers_overall = current_peak
    
    overall_average_viewers = total_average_viewers_sum / stream_count if stream_count > 0 else 0
    
    # Note: aggregated_hourly_stats contains all individual hourly stat objects from all streams in the period.
    # This might be too granular for a summary but useful for detailed PDF tables or combined charts.
    # For a summary chart, we might need to average per hour across days or sum viewers per day.
    
    return {
        "period_name": period_name,
        "start_date": start_date,
        "streams_in_period": streams_in_period, # List of Stream objects
        "aggregated_hourly_stats": aggregated_hourly_stats, # List of all HourlyStat objects in period
        "total_subscriptions_period": total_subscriptions_period,
        "total_donations_period": total_donations_period,
        "total_bits_period": total_bits_period,
        "overall_average_viewers": overall_average_viewers, # Average of average viewers per stream
        "total_peak_viewers_overall": total_peak_viewers_overall, # Highest peak viewers in any stream in period
        "stream_count": stream_count
    }

# Add more analysis functions as needed, e.g., for specific trends, user activity etc.
