from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
import httpx
import pika
import json
import os

from schemas import ReservaRequest, ReservaResponse

from models import Reserva, Base
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Reservation Service")



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
        response = httpx.get(f"http://hotel-service:8000/hoteis/{reserva.id_hotel}")
        hotel = response.json()
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Hotel não encontrado")
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Erro ao comunicar com serviço de hotéis")
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Erro ao comunicar com serviço de hotéis")

    valor_total_reserva = hotel["valor_dia"] * reserva.dias_permanencia
    nome_hotel = hotel["nome"]
    # Salva reserva
    nova_reserva = Reserva(
        id_hotel=reserva.id_hotel,
        nome_usuario=reserva.nome_usuario,
        email_usuario=reserva.email_usuario,  
        cep=reserva.cep,
        data_checkin=reserva.data_checkin,
        data_checkout=reserva.data_checkout,
        dias_permanencia=reserva.dias_permanencia,
        valor_total_reserva=valor_total_reserva

    )
     
    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)

    # Envia para fila de pagamentos
    mensagem = {
        "id_reserva": nova_reserva.id,
        "valor_total_reserva": float(nova_reserva.valor_total_reserva),
        "nome_usuario": reserva.nome_usuario,
        "email_usuario": reserva.email_usuario, 
        "data_checkin": reserva.data_checkin.isoformat(),
        "data_checkout": reserva.data_checkout.isoformat(),
        "nome_hotel": nome_hotel
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