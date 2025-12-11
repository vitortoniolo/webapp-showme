# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl, EmailStr, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

import os
import hashlib
import secrets

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
ADMIN_EMAILS = {
    email.strip().lower()
    for email in (os.getenv("ADMIN_EMAILS") or "").split(",")
    if email.strip()
}
FULL_ACCESS_EMAILS = {
    email.strip().lower()
    for email in (os.getenv("FULL_ACCESS_EMAILS") or "").split(",")
    if email.strip()
}
FULL_ACCESS_EMAILS.add("js.vitortoniolo@hotmail.com")

# Engine / Session (síncrono)
engine = create_engine(DATABASE_URL, echo=True)  # set echo=False em produção
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    events = relationship("Event", back_populates="owner")
    establishments = relationship("Establishment", back_populates="owner")
    tokens = relationship(
        "SessionToken", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_admin(self) -> bool:
        email = (self.email or "").strip().lower()
        return bool(email) and email in ADMIN_EMAILS


class SessionToken(Base):
    __tablename__ = "session_tokens"
    token = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tokens")


class Establishment(Base):
    __tablename__ = "establishments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    capacity = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    events = relationship("Event", back_populates="establishment", cascade="all,delete")
    owner = relationship("User", back_populates="establishments")


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
    image_url = Column(String(255), nullable=True)
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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    establishment = relationship("Establishment", back_populates="events")
    genres = relationship(
        "Genre", secondary=event_genres_table, back_populates="events", viewonly=False
    )
    artists = relationship(
        "Artist", secondary=event_artists_table, back_populates="events", viewonly=False
    )
    owner = relationship("User", back_populates="events")


# === Schemas Pydantic ===
class EventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    date: Optional[datetime] = None
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = Field(default=None, max_length=255)
    image_url: Optional[HttpUrl] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    neighborhood: Optional[str] = Field(default=None, max_length=100)
    street: Optional[str] = Field(default=None, max_length=255)
    number: Optional[str] = Field(default=None, max_length=20)
    price: Optional[float] = None
    url: Optional[HttpUrl] = Field(default=None, max_length=255)
    is_free: Optional[bool] = False
    capacity: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None

class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    date: Optional[datetime] = None
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = Field(default=None, max_length=255)
    image_url: Optional[HttpUrl] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    neighborhood: Optional[str] = Field(default=None, max_length=100)
    street: Optional[str] = Field(default=None, max_length=255)
    number: Optional[str] = Field(default=None, max_length=20)
    price: Optional[float] = None
    url: Optional[HttpUrl] = Field(default=None, max_length=255)
    is_free: Optional[bool] = None
    capacity: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventRead(ORMModel):
    id: int
    establishment_id: Optional[int] = None
    establishment_name: Optional[str] = None
    image_url: Optional[HttpUrl] = None
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
    user_id: Optional[int] = None

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(ORMModel, UserBase):
    id: int
    is_admin: bool = False

class AuthResponse(BaseModel):
    token: str
    user: UserRead


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

security = HTTPBearer(auto_error=False)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_admin_user(user: Optional["User"]) -> bool:
    return bool(user) and bool(getattr(user, "is_admin", False))


def has_full_access_user(user: Optional["User"]) -> bool:
    email = (getattr(user, "email", "") or "").strip().lower()
    return bool(email) and email in FULL_ACCESS_EMAILS


def has_global_editing_access(user: Optional["User"]) -> bool:
    return is_admin_user(user) or has_full_access_user(user)


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return hash_password(plain_password) == password_hash


def create_session_token(user: User, db: Session) -> str:
    token_value = secrets.token_hex(32)
    db_token = SessionToken(token=token_value, user_id=user.id)
    db.add(db_token)
    db.commit()
    return token_value


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    token_value = None
    if credentials:
        token_value = credentials.credentials
    if not token_value and request is not None:
        token_value = request.headers.get("X-Session-Token")
    if not token_value and request is not None:
        token_value = request.query_params.get("token")
    if not token_value:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    session_token = (
        db.query(SessionToken).filter(SessionToken.token == token_value).first()
    )
    if not session_token:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    session_token.last_used_at = datetime.utcnow()
    db.commit()
    return session_token.user

# Cria tabelas no startup (útil para dev)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_event_location_columns()
    ensure_establishment_optional_columns()

# Health
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail j�� cadastrado")
    user = User(
        email=email,
        name=(payload.name or "").strip() or None,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session_token(user, db)
    return {"token": token, "user": user}


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inv��lidas")
    token = create_session_token(user, db)
    return {"token": token, "user": user}


@app.get("/auth/me", response_model=UserRead)
def auth_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Autentica��o necess��ria")
    db.query(SessionToken).filter(SessionToken.token == credentials.credentials).delete()
    db.commit()
    return {"detail": "Logout realizado"}

# Create event
@app.post("/events", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.dict(exclude_unset=True)
    genre_ids = data.pop("genre_ids", None)
    artist_ids = data.pop("artist_ids", None)
    can_manage_all = has_global_editing_access(current_user)

    establishment_id = data.get("establishment_id")
    if establishment_id:
        est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estabelecimento n��o encontrado")
        if est.owner_id and est.owner_id != current_user.id and not can_manage_all:
            raise HTTPException(status_code=403, detail="Estabelecimento pertence a outro usu��rio")
        if est.owner_id is None:
            est.owner_id = current_user.id

    data["user_id"] = current_user.id
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


@app.get("/my/events", response_model=List[EventRead])
def list_my_events(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = db.query(Event)
    if not has_global_editing_access(current_user):
        query = query.filter(Event.user_id == current_user.id)
    events = query.order_by(Event.created_at.desc()).all()
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
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento nǜo encontrado")
    can_manage_all = has_global_editing_access(current_user)
    if event.user_id and event.user_id != current_user.id and not can_manage_all:
        raise HTTPException(status_code=403, detail="VocǦ nǜo pode editar este evento")
    if event.user_id is None:
        event.user_id = current_user.id

    data = payload.dict(exclude_unset=True)
    genre_ids = data.pop("genre_ids", None)
    artist_ids = data.pop("artist_ids", None)
    establishment_id = data.get("establishment_id")
    if establishment_id:
        est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estabelecimento nǜo encontrado")
        if est.owner_id and est.owner_id != current_user.id and not can_manage_all:
            raise HTTPException(status_code=403, detail="Estabelecimento pertence a outro usuǭrio")
        if est.owner_id is None:
            est.owner_id = current_user.id

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
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento nǜo encontrado")
    can_manage_all = has_global_editing_access(current_user)
    if event.user_id and event.user_id != current_user.id and not can_manage_all:
        raise HTTPException(status_code=403, detail="VocǦ nǜo pode excluir este evento")
    db.delete(event)
    db.commit()
    return None 


def serialize_event(e: "Event") -> dict:
    establishment = e.establishment
    return {
        "id": e.id,
        "establishment_id": e.establishment_id,
        "establishment_name": e.establishment_name or (establishment.name if establishment else None),
        "image_url": e.image_url,
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
        "user_id": e.user_id,
    }


def ensure_event_location_columns():
    inspector = inspect(engine)
    if not inspector.has_table("events"):
        return
    existing_columns = {col["name"] for col in inspector.get_columns("events")}
    statements = []
    if "establishment_name" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS establishment_name VARCHAR(255)")
    if "image_url" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS image_url VARCHAR(255)")
    if "city" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS city VARCHAR(100)")
    if "neighborhood" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100)")
    if "street" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS street VARCHAR(255)")
    if "number" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS number VARCHAR(20)")
    if "user_id" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS user_id INTEGER")
    if not statements:
        return
    ddl = "ALTER TABLE events " + ", ".join(statements)
    with engine.begin() as conn:
        conn.execute(text(ddl))


def ensure_establishment_optional_columns():
    inspector = inspect(engine)
    if not inspector.has_table("establishments"):
        return
    existing_columns = {col["name"] for col in inspector.get_columns("establishments")}
    statements = []
    if "image_url" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS image_url VARCHAR(255)")
    if "owner_id" not in existing_columns:
        statements.append("ADD COLUMN IF NOT EXISTS owner_id INTEGER")
    if not statements:
        return
    ddl = "ALTER TABLE establishments " + ", ".join(statements)
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
        image_url="https://images.unsplash.com/photo-1514525253161-7a46d19cd819",
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
        image_url="https://images.unsplash.com/photo-1507878866276-a947ef722fee",
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
        image_url="https://images.unsplash.com/photo-1489515217757-5fd1be406fef",
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
        image_url="https://images.unsplash.com/photo-1504805572947-34fad45aed93",
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
        image_url="https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=900&q=60",
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
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    neighborhood: Optional[str] = Field(default=None, max_length=100)
    street: Optional[str] = Field(default=None, max_length=255)
    number: Optional[str] = Field(default=None, max_length=20)
    capacity: Optional[int] = None

class EstablishmentCreate(EstablishmentBase):
    pass

class EstablishmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    neighborhood: Optional[str] = Field(default=None, max_length=100)
    street: Optional[str] = Field(default=None, max_length=255)
    number: Optional[str] = Field(default=None, max_length=20)
    capacity: Optional[int] = None

class EstablishmentRead(ORMModel, EstablishmentBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class GenreCreate(BaseModel):
    name: str = Field(..., max_length=100)

class GenreUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)

class GenreRead(ORMModel):
    id: int
    name: str

class ArtistCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    url: Optional[HttpUrl] = Field(default=None, max_length=255)

class ArtistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    url: Optional[HttpUrl] = Field(default=None, max_length=255)

class ArtistRead(ORMModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================
# CRUD: Establishments
# =========================
@app.post("/establishments", response_model=EstablishmentRead, status_code=201)
def create_establishment(
    payload: EstablishmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.dict(exclude_unset=True)
    data["owner_id"] = current_user.id
    est = Establishment(**data)
    db.add(est)
    db.commit()
    db.refresh(est)
    return est


@app.get("/establishments", response_model=List[EstablishmentRead])
def list_establishments(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Establishment).offset(skip).limit(limit).all()


@app.get("/my/establishments", response_model=List[EstablishmentRead])
def list_my_establishments(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = db.query(Establishment)
    if not has_global_editing_access(current_user):
        query = query.filter(Establishment.owner_id == current_user.id)
    return query.order_by(Establishment.created_at.desc()).all()


@app.get("/establishments/{establishment_id}", response_model=EstablishmentRead)
def get_establishment(establishment_id: int, db: Session = Depends(get_db)):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    return est


@app.put("/establishments/{establishment_id}", response_model=EstablishmentRead)
def update_establishment(
    establishment_id: int,
    payload: EstablishmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    can_manage_all = has_global_editing_access(current_user)
    if est.owner_id and est.owner_id != current_user.id and not can_manage_all:
        raise HTTPException(status_code=403, detail="Você não pode editar este estabelecimento")
    if est.owner_id is None:
        est.owner_id = current_user.id
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(est, key, value)
    db.commit()
    db.refresh(est)
    return est


@app.delete("/establishments/{establishment_id}", status_code=204)
def delete_establishment(
    establishment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    est = db.query(Establishment).filter(Establishment.id == establishment_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")
    can_manage_all = has_global_editing_access(current_user)
    if est.owner_id and est.owner_id != current_user.id and not can_manage_all:
        raise HTTPException(status_code=403, detail="Você não pode excluir este estabelecimento")
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
