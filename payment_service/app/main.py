from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import pika
import json
import threading
import time
import os

from models import Pagamento, Base
from database import SessionLocal, engine

app = FastAPI(title="Payment Service")

# Schemas
class PagamentoResponse(BaseModel):
    id: int
    id_reserva: int
    valor: float
    status: str

    class Config:
        from_attributes = True

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Tabelas de pagamento criadas/verificadas")
    threading.Thread(target=iniciar_consumidor, daemon=True).start()

# Routes
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "payment-service"}

@app.get("/pagamentos", response_model=List[PagamentoResponse])
def listar_pagamentos(db: Session = Depends(get_db)):
    return db.query(Pagamento).all()

# RabbitMQ Consumer
def conectar_rabbitmq():
    rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbit_url))
            print("✓ Conectado ao RabbitMQ!")
            return connection
        except Exception as e:
            print(f"Aguardando RabbitMQ... ({e})")
            time.sleep(3)

def iniciar_consumidor():
    connection = conectar_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='pagamentos_queue', durable=True)

    def callback(ch, method, properties, body):
        try:
            dados = json.loads(body)
            print(f"📩 MENSAGEM RECEBIDA - Reserva: {dados['id_reserva']}")

            print("⏳ Processando pagamento (aguarde 5 segundos)...")
            time.sleep(5)

            db = SessionLocal()
            pagamento = Pagamento(
                id_reserva=dados['id_reserva'],
                valor= dados['valor_total_reserva'],
                status="Aprovado"
            )
            db.add(pagamento)
            db.commit()
            db.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("✓ Pagamento processado com sucesso")
        except Exception as e:
            print(f"Erro ao processar pagamento: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='pagamentos_queue', on_message_callback=callback)
    print("Consumidor ativo! Aguardando mensagens...")
    channel.start_consuming()