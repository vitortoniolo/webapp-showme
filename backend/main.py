# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
import os

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# === Configuração do DB (troque a URL via variável de ambiente se precisar) ===
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://postgres:test@localhost:5432/eventos_db"
)

# Engine / Session (síncrono)[]
engine = create_engine(DATABASE_URL, echo=True)  # set echo=False em produção
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# === Modelo ORM simples ===
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    city = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    url = Column(String(255), nullable=True)

# === Schemas Pydantic ===
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    city: Optional[str] = None
    price: Optional[float] = None
    url: Optional[HttpUrl] = None

class EventRead(EventCreate):
    id: int

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

# Run (apenas para dev; em produção use uvicorn/gunicorn externamente)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
