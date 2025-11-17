# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Table,
    inspect,
    text,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine / Session (síncrono)
engine = create_engine(DATABASE_URL, echo=True)  # set echo=False em produção
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# === Modelos ORM ===

# Tabela de associação N:N entre eventos e gêneros
event_genres_table = Table(
    "event_genres",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

# Tabela de associação N:N entre eventos e artistas
event_artists_table = Table(
    "event_artists",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True),
)


class Establishment(Base):
    __tablename__ = "establishments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    capacity = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    events = relationship("Event", back_populates="establishment", cascade="all,delete")


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

    events = relationship(
        "Event", secondary=event_genres_table, back_populates="genres", viewonly=False
    )


class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    events = relationship(
        "Event", secondary=event_artists_table, back_populates="artists", viewonly=False
    )


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    establishment_id = Column(
        Integer, ForeignKey("establishments.id", ondelete="SET NULL"), nullable=True
    )
    establishment_name = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    price = Column(Float, nullable=True)
    is_free = Column(Boolean, default=False)
    capacity = Column(Integer, nullable=True)
    url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    establishment = relationship("Establishment", back_populates="events")
    genres = relationship(
        "Genre", secondary=event_genres_table, back_populates="events", viewonly=False
    )
    artists = relationship(
        "Artist", secondary=event_artists_table, back_populates="events", viewonly=False
    )


# === Schemas Pydantic ===
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    price: Optional[float] = None
    url: Optional[HttpUrl] = None
    is_free: Optional[bool] = False
    capacity: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    price: Optional[float] = None
    url: Optional[HttpUrl] = None
    is_free: Optional[bool] = None
    capacity: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None

class EventRead(BaseModel):
    id: int
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    price: Optional[float] = None
    url: Optional[HttpUrl] = None
    is_free: bool
    capacity: Optional[int] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None

    class Config:
        orm_mode = True


# === App ===
app = FastAPI(title="ShowMe - Eventos", version="0.1.0")

# CORS (ajuste allowed_origins conforme o front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
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
    ensure_event_location_columns()

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# Create event
@app.post("/events", response_model=EventRead, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    data = payload.dict(exclude_unset=True)
    genre_ids = data.pop("genre_ids", None)
    artist_ids = data.pop("artist_ids", None)

    db_event = Event(**data)

    if genre_ids:
        genres = db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
        db_event.genres = genres
    if artist_ids:
        artists = db.query(Artist).filter(Artist.id.in_(artist_ids)).all()
        db_event.artists = artists

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return serialize_event(db_event)

# List events
@app.get("/events", response_model=List[EventRead])
def list_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(Event).offset(skip).limit(limit).all()
    return [serialize_event(e) for e in events]

# Get event by id
@app.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return serialize_event(event)

# Update event
@app.put("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    data = payload.dict(exclude_unset=True)
    genre_ids = data.pop("genre_ids", None)
    artist_ids = data.pop("artist_ids", None)

    for key, value in data.items():
        setattr(event, key, value)

    if genre_ids is not None:
        event.genres = db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
    if artist_ids is not None:
        event.artists = db.query(Artist).filter(Artist.id.in_(artist_ids)).all()

    db.commit()
    db.refresh(event)
    return serialize_event(event)

@app.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    db.delete(event)
    db.commit()
    return None 


def serialize_event(e: "Event") -> dict:
    establishment = e.establishment
    return {
        "id": e.id,
        "establishment_id": e.establishment_id,
        "establishment_name": e.establishment_name or (establishment.name if establishment else None),
        "title": e.title,
        "description": e.description,
        "date": e.date,
        "price": e.price,
        "url": e.url,
        "is_free": e.is_free,
        "capacity": e.capacity,
        "city": e.city or (establishment.city if establishment else None),
        "neighborhood": e.neighborhood or (establishment.neighborhood if establishment else None),
        "street": e.street or (establishment.street if establishment else None),
        "number": e.number or (establishment.number if establishment else None),
        "created_at": e.created_at,
        "updated_at": e.updated_at,
        "genre_ids": [g.id for g in (e.genres or [])],
        "artist_ids": [a.id for a in (e.artists or [])],
    }


def ensure_event_location_columns():
    inspector = inspect(engine)
    if not inspector.has_table("events"):
        return
    existing_columns = {col["name"] for col in inspector.get_columns("events")}
    statements = []
    if "establishment_name" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS establishment_name VARCHAR(255)")
    if "city" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS city VARCHAR(100)")
    if "neighborhood" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100)")
    if "street" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS street VARCHAR(255)")
    if "number" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS number VARCHAR(20)")
    if not statements:
        return
    ddl = "ALTER TABLE events " + ", ".join(statements)
    with engine.begin() as conn:
        conn.execute(text(ddl))


# ==========================
# Seed (popular dados de teste)
# ==========================
def _get_or_create_genre(db: Session, name: str) -> Genre:
    g = db.query(Genre).filter(Genre.name == name).first()
    if not g:
        g = Genre(name=name)
        db.add(g)
        db.flush()
    return g


def _get_or_create_establishment(db: Session, name: str, **kwargs) -> Establishment:
    est = db.query(Establishment).filter(Establishment.name == name).first()
    if not est:
        est = Establishment(name=name, **kwargs)
        db.add(est)
        db.flush()
    return est


def _get_or_create_artist(db: Session, name: str, **kwargs) -> Artist:
    art = db.query(Artist).filter(Artist.name == name).first()
    if not art:
        art = Artist(name=name, **kwargs)
        db.add(art)
        db.flush()
    return art


def seed_data(db: Session) -> dict:
    # se já houver eventos, presume-se que já foi populado
    if db.query(Event).count() > 0:
        return {"message": "Já populado", "events": db.query(Event).count()}

    rock = _get_or_create_genre(db, "Rock")
    mpb = _get_or_create_genre(db, "MPB")
    jazz = _get_or_create_genre(db, "Jazz")
    indie = _get_or_create_genre(db, "Indie")

    casa_central = _get_or_create_establishment(
        db,
        "Casa Central",
        description="Espaço para shows de médio porte",
        city="Porto Alegre",
        neighborhood="Centro",
        street="Rua das Artes",
        number="123",
        capacity=800,
    )

    bar_do_bairro = _get_or_create_establishment(
        db,
        "Bar do Bairro",
        description="Palco intimista para acústicos",
        city="Porto Alegre",
        neighborhood="Bom Fim",
        street="Av. Cultural",
        number="45",
        capacity=150,
    )

    banda_alpha = _get_or_create_artist(
        db,
        "Banda Alpha",
        description="Quarteto de rock alternativo",
        url="https://example.com/banda-alpha",
    )

    dj_beta = _get_or_create_artist(
        db,
        "DJ Beta",
        description="Set eclético de indie/eletrônico",
        url="https://example.com/dj-beta",
    )

    quartet_jazz = _get_or_create_artist(
        db,
        "Quarteto Jazz",
        description="Clássicos e standards",
        url="https://example.com/quarteto-jazz",
    )

    # Eventos de exemplo
    ev1 = Event(
        title="Noite Rock Alternativo",
        description="Apresentação da Banda Alpha",
        date=datetime.utcnow(),
        price=30.0,
        is_free=False,
        capacity=400,
        url="https://example.com/evento/rock",
        establishment_id=casa_central.id,
        genres=[rock, indie],
        artists=[banda_alpha],
    )

    ev2 = Event(
        title="Sessão Jazz de Domingo",
        description="Improvisos com Quarteto Jazz",
        date=datetime.utcnow(),
        price=None,
        is_free=True,
        capacity=120,
        url="https://example.com/evento/jazz",
        establishment_id=bar_do_bairro.id,
        genres=[jazz],
        artists=[quartet_jazz],
    )

    ev3 = Event(
        title="Indie Night com DJ Beta",
        description="Pistas com indie/eletrônico",
        date=datetime.utcnow(),
        price=20.0,
        is_free=False,
        capacity=200,
        url="https://example.com/evento/indie",
        establishment_id=bar_do_bairro.id,
        genres=[indie],
        artists=[dj_beta],
    )

    db.add_all([ev1, ev2, ev3])
    db.commit()

    return {
        "message": "Base populada com dados de teste",
        "establishments": db.query(Establishment).count(),
        "genres": db.query(Genre).count(),
        "artists": db.query(Artist).count(),
        "events": db.query(Event).count(),
    }


@app.post("/dev/seed")
def dev_seed(db: Session = Depends(get_db)):
    """Endpoint de conveniência para popular dados de desenvolvimento."""
    return seed_data(db)


# =====================
# Schemas: Establishment
# =====================
class EstablishmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    capacity: Optional[int] = None

class EstablishmentCreate(EstablishmentBase):
    pass

class EstablishmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    capacity: Optional[int] = None

class EstablishmentRead(EstablishmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ========
# Schemas: Genre
# ========
class GenreCreate(BaseModel):
    name: str

class GenreUpdate(BaseModel):
    name: Optional[str] = None

class GenreRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# =========
# Schemas: Artist
# =========
class ArtistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None

class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[HttpUrl] = None

class ArtistRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# =========================
# CRUD: Establishments
# =========================
@app.post("/establishments", response_model=EstablishmentRead, status_code=201)
def create_establishment(payload: EstablishmentCreate, db: Session = Depends(get_db)):
    est = Establishment(**payload.dict(exclude_unset=True))
    db.add(est)
    db.commit()
    db.refresh(est)
    return est


@app.get("/establishments", response_model=List[EstablishmentRead])
def list_establishments(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Establishment).offset(skip).limit(limit).all()


@app.get("/establishments/{establishment_id}", response_model=EstablishmentRead)
def get_establishment(establishment_id: int, db: Session = Depends(get_db)):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    return est


@app.put("/establishments/{establishment_id}", response_model=EstablishmentRead)
def update_establishment(establishment_id: int, payload: EstablishmentUpdate, db: Session = Depends(get_db)):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(est, key, value)
    db.commit()
    db.refresh(est)
    return est


@app.delete("/establishments/{establishment_id}", status_code=204)
def delete_establishment(establishment_id: int, db: Session = Depends(get_db)):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    db.delete(est)
    db.commit()
    return None


# =============
# CRUD: Genres
# =============
@app.post("/genres", response_model=GenreRead, status_code=201)
def create_genre(payload: GenreCreate, db: Session = Depends(get_db)):
    genre = Genre(**payload.dict(exclude_unset=True))
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre


@app.get("/genres", response_model=List[GenreRead])
def list_genres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Genre).offset(skip).limit(limit).all()


@app.get("/genres/{genre_id}", response_model=GenreRead)
def get_genre(genre_id: int, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Gênero não encontrado")
    return genre


@app.put("/genres/{genre_id}", response_model=GenreRead)
def update_genre(genre_id: int, payload: GenreUpdate, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Gênero não encontrado")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(genre, key, value)
    db.commit()
    db.refresh(genre)
    return genre


@app.delete("/genres/{genre_id}", status_code=204)
def delete_genre(genre_id: int, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Gênero não encontrado")
    db.delete(genre)
    db.commit()
    return None


# =============
# CRUD: Artists
# =============
@app.post("/artists", response_model=ArtistRead, status_code=201)
def create_artist(payload: ArtistCreate, db: Session = Depends(get_db)):
    artist = Artist(**payload.dict(exclude_unset=True))
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return artist


@app.get("/artists", response_model=List[ArtistRead])
def list_artists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Artist).offset(skip).limit(limit).all()


@app.get("/artists/{artist_id}", response_model=ArtistRead)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artista não encontrado")
    return artist


@app.put("/artists/{artist_id}", response_model=ArtistRead)
def update_artist(artist_id: int, payload: ArtistUpdate, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artista não encontrado")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(artist, key, value)
    db.commit()
    db.refresh(artist)
    return artist


@app.delete("/artists/{artist_id}", status_code=204)
def delete_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artista não encontrado")
    db.delete(artist)
    db.commit()
    return None



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Erro de validação:", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
