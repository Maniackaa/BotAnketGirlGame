"""SQLAlchemy модели для базы данных"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    ForeignKey, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    rules_accepted = Column(Boolean, default=False)
    rules_accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user")


class Profile(Base):
    """Модель анкеты девушки"""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    audio_chat_price = Column(Float, nullable=False)  # Цена за час
    video_chat_price = Column(Float, nullable=False)  # Цена за час
    private_price = Column(Float, nullable=True)  # Цена за месяц
    channel_link = Column(String(255), nullable=True)  # Ссылка на канал
    photo_ids = Column(JSON, nullable=True)  # Список file_id фотографий
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    games = relationship("ProfileGame", back_populates="profile", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="profile")


class Game(Base):
    """Модель игры"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profiles = relationship("ProfileGame", back_populates="game")


class ProfileGame(Base):
    """Связь между анкетами и играми (многие ко многим)"""
    __tablename__ = "profile_games"
    
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    
    profile = relationship("Profile", back_populates="games")
    game = relationship("Game", back_populates="profiles")


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # #321
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    format_type = Column(String(50), nullable=False)  # "audio" или "video"
    game_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    game_name = Column(String(255), nullable=True)  # Название игры на момент заказа
    
    date = Column(DateTime, nullable=False)
    duration_hours = Column(Float, nullable=False)
    participants_count = Column(Integer, nullable=False, default=1)
    
    base_price = Column(Float, nullable=False)  # Базовая цена
    additional_participants_price = Column(Float, default=0)  # Доплата за участников
    total_price = Column(Float, nullable=False)  # Итоговая цена
    
    payment_status = Column(String(50), default="not_paid")  # not_paid, processing, paid
    conference_link = Column(Text, nullable=True)  # Ссылка на конференцию
    
    reminder_sent = Column(Boolean, default=False)  # Отправлено ли напоминание за 15 мин
    notification_enabled = Column(Boolean, default=True)  # Включены ли уведомления
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    profile = relationship("Profile", back_populates="orders")
    game = relationship("Game")
    reminder_tasks = relationship("ReminderTask", back_populates="order", cascade="all, delete-orphan")


class ReminderTask(Base):
    """Модель задачи напоминания для APScheduler"""
    __tablename__ = "reminder_tasks"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), nullable=False)  # "reminder_15min", "after_meeting", "check_payment"
    scheduled_time = Column(DateTime, nullable=False, index=True)
    job_id = Column(String(255), nullable=True)  # ID задачи в APScheduler
    executed = Column(Boolean, default=False)  # Выполнена ли задача
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="reminder_tasks")

