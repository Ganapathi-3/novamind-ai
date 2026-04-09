
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String(50),  unique=True, index=True, nullable=False)
    email            = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password  = Column(String(255), nullable=False)
    role             = Column(String(20),  default="intern", nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    chat_history     = relationship("ChatHistory", back_populates="user")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    question  = Column(Text, nullable=False)
    answer    = Column(Text, nullable=False)
    sources   = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user      = relationship("User", back_populates="chat_history")
