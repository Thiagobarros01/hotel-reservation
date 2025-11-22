from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import httpx

from models import Hotel, Base
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Hotel Service")

# Schemas
class HotelRequest(BaseModel):
    nome: str
    localizacao: str
    salas_disponiveis: int

class HotelResponse(BaseModel):
    id: int
    nome: str
    localizacao: str
    salas_disponiveis: int

    class Config:
        from_attributes = True

class EnderecoResponse(BaseModel):
    logradouro: str
    bairro: str
    localidade: str
    uf: str

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "hotel-service"}

@app.post("/hoteis", response_model=HotelResponse)
def criar_hotel(hotel: HotelRequest, db: Session = Depends(get_db)):
    novo_hotel = Hotel(**hotel.dict())
    db.add(novo_hotel)
    db.commit()
    db.refresh(novo_hotel)
    return novo_hotel

@app.get("/hoteis", response_model=List[HotelResponse])
def listar_hoteis(db: Session = Depends(get_db)):
    return db.query(Hotel).all()

@app.get("/cep/{cep}", response_model=EnderecoResponse)
async def buscar_cep(cep: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://viacep.com.br/ws/{cep}/json/")
        if response.status_code != 200 or "erro" in response.json():
            raise HTTPException(404, "CEP não encontrado")
        data = response.json()
        return EnderecoResponse(
            logradouro=data["logradouro"],
            bairro=data["bairro"],
            localidade=data["localidade"],
            uf=data["uf"]
        )