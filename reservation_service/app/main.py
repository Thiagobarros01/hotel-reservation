from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
import httpx
import pika
import json
import os

from models import Reserva, Base
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Reservation Service")

# Schemas
class ReservaRequest(BaseModel):
    id_hotel: int
    nome_usuario: str
    email_usuario: str
    cep: str
    data_checkin: date
    data_checkout: date

class ReservaResponse(BaseModel):
    id: int
    id_hotel: int
    nome_usuario: str
    data_checkin: date
    data_checkout: date

    class Config:
        from_attributes = True

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
    return {"status": "healthy", "service": "reservation-service"}

@app.post("/reservas", response_model=ReservaResponse)
def criar_reserva(reserva: ReservaRequest, db: Session = Depends(get_db)):
    # Verifica se hotel existe
    try:
        response = httpx.get("http://hotel-service:8000/hoteis")
        hoteis = response.json()
        if not any(h["id"] == reserva.id_hotel for h in hoteis):
            raise HTTPException(404, "Hotel não encontrado")
    except Exception:
        raise HTTPException(503, "Serviço de hotéis indisponível")

    # Salva reserva
    nova_reserva = Reserva(
        id_hotel=reserva.id_hotel,
        nome_usuario=reserva.nome_usuario,
        email_usuario=reserva.email_usuario,  
        cep=reserva.cep,
        data_checkin=reserva.data_checkin,
        data_checkout=reserva.data_checkout
    )
    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)

    # Envia para fila de pagamentos
    mensagem = {
        "id_reserva": nova_reserva.id,
        "valor": 350.00,
        "nome_usuario": reserva.nome_usuario,
        "email_usuario": reserva.email_usuario, 
        "data_checkin": reserva.data_checkin.isoformat(),
        "data_checkout": reserva.data_checkout.isoformat()
    }
    
    try:
        rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        connection = pika.BlockingConnection(pika.URLParameters(rabbit_url))
        channel = connection.channel()
        channel.queue_declare(queue='pagamentos_queue', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='pagamentos_queue',
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        channel.queue_declare(queue='notificacoes_queue', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='notificacoes_queue',
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print("Mensagem enviada também para fila de notificações!")
        connection.close()
    except Exception as e:
        print(f"Erro ao enviar para RabbitMQ: {e}")

    return nova_reserva

@app.get("/reservas", response_model=list[ReservaResponse])
def listar_reservas(db: Session = Depends(get_db)):
    return db.query(Reserva).all()