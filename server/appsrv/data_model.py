from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

db = SQLAlchemy()

@dataclass
class Card(db.Model):

    __tablename__ = "cards"

    id: int = db.Column(db.Integer, primary_key=True)
    card_id: int = db.Column(db.String)
    date_init: str = db.Column(db.String)
    water_type: str = db.Column(db.Integer)
    total_limit: str = db.Column(db.Integer)
    total_left: str = db.Column(db.Integer)
    daily_limit: str = db.Column(db.Integer)
    daily_left: str = db.Column(db.Integer)
    realese_count: str = db.Column(db.Integer)
    
    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'card_id': self.card_id,
            'date_init': self.date_init,
            'water_type': self.water_type,
            'total_limit': self.total_limit,
            'total_left': self.total_left,
            'daily_limit': self.daily_limit,
            'daily_left': self.daily_left,
            'realese_count': self.realese_count,
        }

