from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


@dataclass
class Card(db.Model):

    __tablename__ = "cards"

    id: int = db.Column(db.Integer, primary_key=True)
    card_id: int = db.Column(db.String)
    date_init: str = db.Column(db.String)
    user_who_init: int = db.Column(db.Integer)
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
            "id": self.id,
            "card_id": self.card_id,
            "date_init": self.date_init,
            "user_who_init": self.user_who_init,
            "water_type": self.water_type,
            "total_limit": self.total_limit,
            "total_left": self.total_left,
            "daily_limit": self.daily_limit,
            "daily_left": self.daily_left,
            "realese_count": self.realese_count,
        }


@dataclass
class User(db.Model):

    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String)
    password: str = db.Column(db.String)
    authenticated: bool = db.Column(db.Boolean, default=False)
    enabled: bool = db.Column(db.Boolean, default=True)

    def is_active(self):
        return True

    def get_id(self):
        return self.name

    def is_authenticated(self):
        return self.authenticated

    def is_anonimous(self):
        return False

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            "id": self.id,
            "name": self.name,
            "password": self.password,
            "authenticated": self.authenticated,
            "enabled": self.enabled,
        }


@dataclass
class Task(db.Model):

    __tablename__ = "tasks"

    id: int = db.Column(db.Integer, primary_key=True)
    create_date: date = db.Column(db.Date)
    completed: bool = db.Column(db.Boolean, nullable=False, default=False)
