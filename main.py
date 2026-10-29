import os
from contextlib import asynccontextmanager
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sinal:sinal_dev@localhost:5432/sinal_acessivel",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    accessibility_needs: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        server_default=text("'{}'"),
    )
    extra_seconds: Mapped[int] = mapped_column(
        Integer,
        default=10,
        server_default=text("10"),
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Intersection(Base):
    __tablename__ = "intersections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    normal_crossing_seconds: Mapped[int] = mapped_column(
        Integer,
        default=20,
        server_default=text("20"),
    )
    max_extra_seconds: Mapped[int] = mapped_column(
        Integer,
        default=30,
        server_default=text("30"),
    )
    simulation_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
    )


class CrossingRequest(Base):
    __tablename__ = "crossing_requests"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    intersection_id: Mapped[UUID] = mapped_column(ForeignKey("intersections.id"))
    requested_extra_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="simulated",
        server_default=text("'simulated'"),
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Use uma senha com pelo menos 12 caracteres.")
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sinal Acessível",
    description="API demonstrativa de acessibilidade urbana",
    version="0.1.0",
    lifespan=lifespan,
)


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    accessibility_needs: list[str] = Field(default_factory=list)


class SimulationInput(BaseModel):
    user_id: UUID
    intersection_id: UUID


@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation"}


@app.post("/api/register", status_code=201)
def register(data: RegisterInput, db: Session = Depends(get_db)):
    email = str(data.email).lower()

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Este e-mail já está cadastrado.")

    allowed_needs = {
        "mobilidade_reduzida",
        "cadeira_de_rodas",
        "deficiencia_visual",
        "outra_necessidade",
    }

    if not data.accessibility_needs:
        raise HTTPException(422, "Selecione pelo menos uma necessidade de acessibilidade.")

    if not set(data.accessibility_needs).issubset(allowed_needs):
        raise HTTPException(422, "Opção de acessibilidade inválida.")

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        accessibility_needs=data.accessibility_needs,
        extra_seconds=10,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "name": user.name,
        "message": "Cadastro criado com sucesso.",
    }


@app.get("/api/intersections")
def intersections(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Intersection).where(Intersection.simulation_enabled.is_(True))
    ).all()

    return [
        {
            "id": str(row.id),
            "name": row.name,
            "normal_seconds": row.normal_crossing_seconds,
            "max_extra_seconds": row.max_extra_seconds,
        }
        for row in rows
    ]


@app.post("/api/demo/simulate")
def simulate(data: SimulationInput, db: Session = Depends(get_db)):
    user = db.get(User, data.user_id)
    intersection = db.get(Intersection, data.intersection_id)

    if not user or not user.active:
        raise HTTPException(404, "Usuário não encontrado ou inativo.")

    if not intersection or not intersection.simulation_enabled:
        raise HTTPException(404, "Cruzamento virtual indisponível.")

    if not user.accessibility_needs:
        raise HTTPException(422, "Configure a necessidade de acessibilidade no cadastro.")

    extra = min(user.extra_seconds, intersection.max_extra_seconds)

    event = CrossingRequest(
        user_id=user.id,
        intersection_id=intersection.id,
        requested_extra_seconds=extra,
        status="simulated",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "mode": "simulation_only",
        "event_id": str(event.id),
        "traffic_light": "VERDE_SIMULADO",
        "normal_seconds": intersection.normal_crossing_seconds,
        "extra_seconds": extra,
        "total_seconds": intersection.normal_crossing_seconds + extra,
        "message": "Simulação concluída. Nenhum semáforo real foi alterado.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
