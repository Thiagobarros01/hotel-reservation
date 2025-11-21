from fastapi import FastAPI
from sqlalchemy.orm import Session
import pika
import json
import threading
import time
import os
from models import Pagamento, Base
from database import SessionLocal, engine

app = FastAPI(title="Payment Service - Hotelaria")

# NÃO cria tabelas aqui no import! Vamos criar só quando a app iniciar
@app.on_event("startup")
def startup_event():
    # Agora sim, cria as tabelas quando a aplicação já está rodando
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas/verificados no banco de pagamentos")
    
    # Inicia o consumidor em background
    threading.Thread(target=iniciar_consumidor, daemon=True).start()

def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"status": "Payment Service rodando e consumindo fila pagamentos_queue..."}

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
            print(f"\nPAGAMENTO RECEBIDO → Reserva: {dados['id_reserva']} | Cliente: {dados['nome_usuario']} | R$ {dados.get('valor', 350.00)}")

            db = SessionLocal()
            pagamento = Pagamento(
                id_reserva=dados['id_reserva'],
                valor=dados.get('valor', 350.00),
                status="Aprovado"
            )
            db.add(pagamento)
            db.commit()
            db.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("Pagamento salvo no banco com sucesso!\n")
        except Exception as e:
            print(f"Erro ao processar pagamento: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='pagamentos_queue', on_message_callback=callback)
    print("Consumidor ativo! Aguardando mensagens na fila pagamentos_queue...")
    channel.start_consuming()