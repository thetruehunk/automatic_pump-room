import os
from dataclasses import dataclass
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import generic_repr
from sqlalchemy.inspection import inspect

engine = create_engine("sqlite:///db/data.db3", echo=False)
Base = declarative_base()

@generic_repr
class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    card_id = Column(String)
    date_init = Column(String)
    water_type = Column(Integer)
    total_limit = Column(Integer)
    daily_limit = Column(Integer)
    current_daily_limit = Column(Integer)
    current_realese_count = Column(Integer)
    total_realese_count = Column(Integer)

#if not engine.dialect.has_table(engine, "cards"):
if not inspect(engine).has_table("cards"):
    Base.metadata.create_all(engine)

