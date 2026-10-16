"""
Chess Trainer Server — серверная часть проекта по ТЗ.
FastAPI + SQLite + SQLAlchemy.
"""
import json
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import desc

from database import SessionLocal
from models import Game, User, Event


app = FastAPI(
    title="Chess Trainer API",
    description="Сервер бизнес-логики шахматного тренажёра",
    version="0.3.0",
)


# ============ PYDANTIC-МОДЕЛИ ============
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class GameCreate(BaseModel):
    player_name: str
    opponent: str
    result: str = "ongoing"
    moves: str = ""


class GameResponse(BaseModel):
    id: int
    player_name: str
    opponent: str
    result: Optional[str]
    moves: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    external_id: str
    platform: str = "telegram"
    username: Optional[str] = None
    first_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    external_id: str
    platform: str
    username: Optional[str]
    first_name: Optional[str]
    theme: str
    notifications: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    source: str
    event_type: str
    user_external_id: Optional[str] = None
    payload: Optional[dict] = None


class EventResponse(BaseModel):
    id: int
    source: str
    event_type: str
    user_external_id: Optional[str]
    processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_users: int
    total_games: int
    total_events: int
    games_today: int
    games_won: int
    games_lost: int
    games_draw: int
    top_opponents: List[dict]


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class BroadcastResponse(BaseModel):
    status: str
    message: str
    recipients: int


# ============ ЗАВИСИМОСТИ ============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ БАЗОВЫЕ ЭНДПОИНТЫ ============
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        version="0.3.0",
    )


@app.get("/")
async def root():
    return {"message": "Chess Trainer Server", "docs": "/docs"}


# ============ ИГРЫ ============
@app.post("/api/v1/games", response_model=GameResponse)
async def create_game(game: GameCreate, db: Session = Depends(get_db)):
    new_game = Game(
        player_name=game.player_name,
        opponent=game.opponent,
        result=game.result,
        moves=game.moves,
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return new_game


@app.get("/api/v1/games/random", response_model=GameResponse)
async def get_random_game(db: Session = Depends(get_db)):
    """Случайная партия из базы (генерация игр)."""
    game = db.query(Game).order_by(func.random()).first()
    if not game:
        raise HTTPException(status_code=404, detail="Партий не найдено")
    return game


@app.get("/api/v1/games/{game_id}", response_model=GameResponse)
async def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Партия не найдена")
    return game


@app.get("/api/v1/games", response_model=List[GameResponse])
async def list_games(limit: int = 20, db: Session = Depends(get_db)):
    """Список последних партий."""
    return db.query(Game).order_by(desc(Game.created_at)).limit(limit).all()


# ============ ПОЛЬЗОВАТЕЛИ ============
@app.post("/api/v1/users", response_model=UserResponse)
async def create_or_get_user(user: UserCreate, db: Session = Depends(get_db)):
    """Создать пользователя или вернуть существующего."""
    existing = db.query(User).filter(User.external_id == user.external_id).first()
    if existing:
        existing.last_seen = datetime.now()
        if user.username: existing.username = user.username
        if user.first_name: existing.first_name = user.first_name
        db.commit()
        db.refresh(existing)
        return existing
    new_user = User(
        external_id=user.external_id,
        platform=user.platform,
        username=user.username,
        first_name=user.first_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.get("/api/v1/users/external/{external_id}", response_model=UserResponse)
async def get_user_by_external(external_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.external_id == external_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


# ============ СОБЫТИЯ ============
@app.post("/api/v1/events", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Приём нормализованного события от клиента."""
    new_event = Event(
        source=event.source,
        event_type=event.event_type,
        user_external_id=event.user_external_id,
        payload=json.dumps(event.payload) if event.payload else None,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


@app.get("/api/v1/events", response_model=List[EventResponse])
async def list_events(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Event).order_by(desc(Event.created_at)).limit(limit).all()


# ============ СТАТИСТИКА ============
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Общая статистика сервера."""
    total_users = db.query(User).count()
    total_games = db.query(Game).count()
    total_events = db.query(Event).count()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    games_today = db.query(Game).filter(Game.created_at >= today_start).count()

    games_won = db.query(Game).filter(Game.result == "win").count()
    games_lost = db.query(Game).filter(Game.result == "lose").count()
    games_draw = db.query(Game).filter(Game.result == "draw").count()

    top = (
        db.query(Game.opponent, func.count(Game.id).label("cnt"))
        .group_by(Game.opponent)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )
    top_opponents = [{"opponent": name, "games": count} for name, count in top]

    return StatsResponse(
        total_users=total_users,
        total_games=total_games,
        total_events=total_events,
        games_today=games_today,
        games_won=games_won,
        games_lost=games_lost,
        games_draw=games_draw,
        top_opponents=top_opponents,
    )


# ============ АДМИНКА ============
@app.post("/api/v1/admin/broadcast", response_model=BroadcastResponse)
async def admin_broadcast(req: BroadcastRequest, db: Session = Depends(get_db)):
    """Рассылка (заглушка — считает пользователей)."""
    users = db.query(User).filter(User.notifications == True).all()
    for u in users:
        new_event = Event(
            source=u.platform,
            event_type="broadcast",
            user_external_id=u.external_id,
            payload=json.dumps({"message": req.message}),
        )
        db.add(new_event)
    db.commit()
    return BroadcastResponse(
        status="queued",
        message=req.message,
        recipients=len(users),
    )