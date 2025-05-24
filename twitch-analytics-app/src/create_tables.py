# filepath: c:\Users\tharu\Downloads\P1\twitch-analytics-app\src\create_tables.py
from database.models import Base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///twitch_analytics.db')
Base.metadata.create_all(engine)