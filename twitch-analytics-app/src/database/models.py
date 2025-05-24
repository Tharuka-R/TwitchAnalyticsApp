from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ViewerCount(Base):
    __tablename__ = 'viewer_counts'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False)

class Follower(Base):
    __tablename__ = 'followers'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False)

class Subscriber(Base):
    __tablename__ = 'subscribers'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False)

class BitDonor(Base):
    __tablename__ = 'bit_donors'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    amount = Column(Integer, nullable=False)

class GiftSubber(Base):
    __tablename__ = 'gift_subbers'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False)

class Donor(Base):
    __tablename__ = 'donors'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    amount = Column(Integer, nullable=False)