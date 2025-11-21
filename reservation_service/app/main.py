from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import date
import httpx
import pika
import json
import os

from models import Reserva, Base
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Reservation Service - Hotelaria")

# --- Schemas ---
class EnderecoResponse(BaseModel):
    logradouro: str
    bairro: str
    localidade: str
    uf: str

class ReservaRequest(BaseModel):
    id_hotel: int
    nome_usuario: str
    cep: str  # Novo campo para ViaCEP
    data_checkin: date
    data_checkout: date

class ReservaResponse(BaseModel):
    id: int
    id_hotel: int
    nome_usuario: str
    data_checkin: date
    data_checkout: date

    model_config = ConfigDict(from_attributes=True)

# --- DB ---
def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ViaCEP (API externa) ---
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

# --- Criar reserva com tudo integrado ---
@app.post("/reservas", response_model=ReservaResponse)
def criar_reserva(reserva: ReservaRequest, db: Session = Depends(obter_db)):
    # 1. Comunicação SÍNCRONA: verifica se hotel existe
    response = httpx.get(f"http://hotel-service:8000/hoteis")
    hoteis = response.json()["hoteis"]
    if not any(h["id"] == reserva.id_hotel for h in hoteis):
        raise HTTPException(404, "Hotel não encontrado")

    # 2. Salva a reserva
    nova_reserva = Reserva(**reserva.dict(exclude={"cep"}))
    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)

    # 3. Comunicação ASSÍNCRONA: manda pro payment-service via RabbitMQ
    mensagem = {
        "id_reserva": nova_reserva.id,
        "valor": 350.00,  # valor fixo só pra demo
        "nome_usuario": reserva.nome_usuario
    }
    
    rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    connection = pika.BlockingConnection(pika.URLParameters(rabbit_url))
    channel = connection.channel()
    channel.queue_declare(queue='pagamentos_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='pagamentos_queue',
        body=json.dumps(mensagem),
        properties=pika.BasicProperties(delivery_mode=2)  # persistente
    )
    connection.close()

    return nova_reserva