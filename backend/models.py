from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    points = Column(Integer, default=0)

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    difficulty = Column(String)
    os = Column(String, default="Linux")
    flag_user = Column(String)
    flag_root = Column(String)

class Solve(Base):
    __tablename__ = "solves"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    type = Column(String)  # user o root
    created_at = Column(DateTime, default=func.now())
