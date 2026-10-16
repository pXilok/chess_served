"""
Модели (таблицы) базы данных.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """Пользователь бота/игры."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True)  # telegram_id или pygame ник
    platform = Column(String(20), default="telegram")  # telegram / vk / pygame
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Настройки (для /settings в боте)
    theme = Column(String(20), default="Classic")
    notifications = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User {self.id}: {self.username or self.external_id}>"


class Game(Base):
    """Одна шахматная партия."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(100), nullable=False)
    opponent = Column(String(100), nullable=False)
    result = Column(String(20), nullable=True)  # win/lose/draw/ongoing
    moves = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)

    # Опциональная связь с User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Game {self.id}: {self.player_name} vs {self.opponent}>"


class Event(Base):
    """Нормализованное событие от клиента (соцсети/игры)."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(30), nullable=False)  # telegram / vk / pygame
    event_type = Column(String(50), nullable=False)  # message / command / callback
    user_external_id = Column(String(100), nullable=True)
    payload = Column(Text, nullable=True)  # JSON с данными
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Event {self.id}: {self.source}/{self.event_type}>"