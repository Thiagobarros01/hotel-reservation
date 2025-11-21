from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import date

# Importando as classes locais
from models import Reserva, Base
from database import SessionLocal, engine

# Cria as tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Schemas Pydantic (Validação) ---

# Modelo para criar reserva (Entrada)
class ReservaRequest(BaseModel):
    id_hotel: int
    nome_usuario: str
    data_checkin: date
    data_checkout: date

# Modelo de resposta (Saída)
class ReservaResponse(BaseModel):
    id: int
    id_hotel: int
    nome_usuario: str
    data_checkin: date
    data_checkout: date

    # Permite conversão direta do SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# Modelo para lista
class ListaReservas(BaseModel):
    reservas: List[ReservaResponse]

# --- Dependência ---

def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas ---

@app.post("/reservas", response_model=ReservaResponse)
def criar_reserva(reserva: ReservaRequest, db: Session = Depends(obter_db)):
    nova_reserva = Reserva(
        id_hotel=reserva.id_hotel,
        nome_usuario=reserva.nome_usuario,
        data_checkin=reserva.data_checkin,
        data_checkout=reserva.data_checkout
    )
    
    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)
    return nova_reserva

@app.get("/reservas", response_model=ListaReservas)
def listar_reservas(db: Session = Depends(obter_db)):
    lista = db.query(Reserva).all()
    return {"reservas": lista}