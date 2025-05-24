def analyze_daily_performance(viewer_data):
    daily_analysis = {}
    for entry in viewer_data:
        date = entry['date']
        if date not in daily_analysis:
            daily_analysis[date] = {
                'total_viewers': 0,
                'total_followers': 0,
                'total_subscribers': 0,
                'total_bit_donors': 0,
                'total_gift_subbers': 0,
                'total_donors': 0
            }
        daily_analysis[date]['total_viewers'] += entry['viewers']
        daily_analysis[date]['total_followers'] += entry['followers']
        daily_analysis[date]['total_subscribers'] += entry['subscribers']
        daily_analysis[date]['total_bit_donors'] += entry['bit_donors']
        daily_analysis[date]['total_gift_subbers'] += entry['gift_subbers']
        daily_analysis[date]['total_donors'] += entry['donors']
    
    return daily_analysis

def analyze_monthly_performance(viewer_data):
    monthly_analysis = {}
    for entry in viewer_data:
        month = entry['date'][:7]  # Extracting YYYY-MM
        if month not in monthly_analysis:
            monthly_analysis[month] = {
                'total_viewers': 0,
                'total_followers': 0,
                'total_subscribers': 0,
                'total_bit_donors': 0,
                'total_gift_subbers': 0,
                'total_donors': 0
            }
        monthly_analysis[month]['total_viewers'] += entry['viewers']
        monthly_analysis[month]['total_followers'] += entry['followers']
        monthly_analysis[month]['total_subscribers'] += entry['subscribers']
        monthly_analysis[month]['total_bit_donors'] += entry['bit_donors']
        monthly_analysis[month]['total_gift_subbers'] += entry['gift_subbers']
        monthly_analysis[month]['total_donors'] += entry['donors']
    
    return monthly_analysis