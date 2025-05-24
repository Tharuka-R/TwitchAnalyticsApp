def insert_data(viewer_data):
    from src.database.models import ViewerCount, Follower, Subscriber, BitDonor, GiftSubber, Donor
    from src.database import db

    # Extract data from the input
    date = viewer_data.get('date')
    viewer_count = viewer_data.get('viewer_count')
    followers = viewer_data.get('followers')
    subscribers = viewer_data.get('subscribers')
    bit_donors = viewer_data.get('bit_donors')
    gift_subbers = viewer_data.get('gift_subbers')
    overall_donors = viewer_data.get('overall_donors')

    # Create instances of the models
    viewer_count_entry = ViewerCount(date=date, count=viewer_count)
    follower_entry = Follower(date=date, count=followers)
    subscriber_entry = Subscriber(date=date, count=subscribers)
    bit_donor_entry = BitDonor(date=date, count=bit_donors)
    gift_subber_entry = GiftSubber(date=date, count=gift_subbers)
    donor_entry = Donor(date=date, count=overall_donors)

    # Insert data into the database
    db.session.add(viewer_count_entry)
    db.session.add(follower_entry)
    db.session.add(subscriber_entry)
    db.session.add(bit_donor_entry)
    db.session.add(gift_subber_entry)
    db.session.add(donor_entry)

    # Commit the session to save the data
    db.session.commit()