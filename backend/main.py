# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

import os

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine / Session (síncrono)
engine = create_engine(DATABASE_URL, echo=True)  # set echo=False em produção
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# === Modelo ORM atualizado ===
class Event(Base):
    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)  # data e hora do começo do evento
    
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)  # bairro
    street = Column(String(255), nullable=True)       # rua
    number = Column(String(20), nullable=True)       # número da rua
    
    price = Column(Float, nullable=True)
    url = Column(String(255), nullable=True)
    
    is_free = Column(Boolean, default=False)  # indica se é gratuito
    capacity = Column(Integer, nullable=True) # limite de participantes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# === Schemas Pydantic ===
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None

    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None

    price: Optional[float] = None
    url: Optional[HttpUrl] = None

    is_free: Optional[bool] = False
    capacity: Optional[int] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None

    price: Optional[float] = None
    url: Optional[HttpUrl] = None

    is_free: Optional[bool] = None
    capacity: Optional[int] = None

class EventRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None

    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None

    price: Optional[float] = None
    url: Optional[HttpUrl] = None

    is_free: bool
    capacity: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# === App ===
app = FastAPI(title="ShowMe - Eventos", version="0.1.0")

# CORS (ajuste allowed_origins conforme o front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cria tabelas no startup (útil para dev)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# Create event
@app.post("/events", response_model=EventRead, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    db_event = Event(**payload.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# List events
@app.get("/events", response_model=List[EventRead])
def list_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(Event).offset(skip).limit(limit).all()
    return events

# Get event by id
@app.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return event

# Update event
@app.put("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event

# Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
