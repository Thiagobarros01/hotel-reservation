from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import httpx

from models import Hotel, Base
from database import SessionLocal, engine
from schemas import HotelRequest, HotelResponse, EnderecoResponse

Base.metadata.create_all(bind=engine) # Cria as tabelas no banco de dados -> ddl-auto=create java
app = FastAPI(title="Hotel Service") # @SpringBootApplication equivalent

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
                     
                     #ResponseEntity<HotelResponse>
@app.post("/hoteis", response_model=HotelResponse)  #Autowired do Java -> HotelRepository repo
def criar_hotel(hotel: HotelRequest, db: Session = Depends(get_db)):
    novo_hotel = Hotel(
        nome=hotel.nome,
        localizacao=hotel.localizacao,
        salas_disponiveis=hotel.salas_disponiveis,
        valor_dia=hotel.valor_dia
    )
    db.add(novo_hotel)
    db.commit()
    db.refresh(novo_hotel)
    return novo_hotel

@app.get("/hoteis", response_model=List[HotelResponse])
def listar_hoteis(db: Session = Depends(get_db)):
    return db.query(Hotel).all()

@app.get("/hoteis/{hotel_id}", response_model=HotelResponse)
def obter_hotel_por_id(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(404, "Hotel não encontrado")
    return hotel

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
    
