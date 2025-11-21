from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, ConfigDict

# Importando as classes locais
from models import Hotel, Base
from database import SessionLocal, engine

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Classes Pydantic (Schemas) ---

# Modelo para receber dados do usuário
class HotelRequest(BaseModel):
    nome: str
    localizacao: str
    salas_disponiveis: int

# Modelo para devolver dados (inclui o ID)
class HotelResponse(BaseModel):
    id: int
    nome: str
    localizacao: str
    salas_disponiveis: int

    # Configuração para compatibilidade com SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# Modelo para listagem
class ListaHoteis(BaseModel):
    hoteis: List[HotelResponse]

# --- Dependências ---

def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas da API ---

@app.post("/hoteis", response_model=HotelResponse)
def criar_hotel(hotel: HotelRequest, db: Session = Depends(obter_db)):
    # Criando objeto do banco com os dados recebidos
    novo_hotel = Hotel(
        nome=hotel.nome,
        localizacao=hotel.localizacao,
        salas_disponiveis=hotel.salas_disponiveis
    )
    
    db.add(novo_hotel)
    db.commit()
    db.refresh(novo_hotel)
    return novo_hotel

@app.get("/hoteis", response_model=ListaHoteis)
def listar_hoteis(db: Session = Depends(obter_db)):
    lista = db.query(Hotel).all()
    return {"hoteis": lista}