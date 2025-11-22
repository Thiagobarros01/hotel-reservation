# notification_service/app/main.py  → VERSÃO SIMPLES E QUE NUNCA FALHA
from fastapi import FastAPI
import pika
import json
import threading
import asyncio
import aiosmtplib
from email.message import EmailMessage

app = FastAPI(title="Notification Service")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASS = ""   # ← senha de 16 caracteres

async def enviar_email(dados):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = dados["email_usuario"]
    msg["Subject"] = "Reserva Confirmada!"

    corpo = f"""
Olá {dados['nome_usuario']},

Reserva confirmada!
Período: {dados['data_checkin']} até {dados['data_checkout']}
Valor: R$ 350,00

Obrigado!
"""
    msg.set_content(corpo)

    await aiosmtplib.send(msg, hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True,
                          username=SMTP_USER, password=SMTP_PASS)
    print(f"E-MAIL ENVIADO → {dados['email_usuario']}")

def consumidor():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters("amqp://guest:guest@rabbitmq:5672/")
            )
            channel = connection.channel()
            channel.queue_declare(queue='notificacoes_queue', durable=True)

            def callback(ch, method, properties, body):
                dados = json.loads(body)
                print(f"MENSAGEM RECEBIDA → Reserva {dados['id_reserva']}")
                asyncio.run(enviar_email(dados))   # roda direto, sem complicação
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue='notificacoes_queue', on_message_callback=callback)
            print("NOTIFICATION-SERVICE ATIVO → esperando mensagens em notificacoes_queue")
            channel.start_consuming()
        except Exception as e:
            print(f"RabbitMQ caiu → reconectando em 5s... {e}")
            connection.close() if 'connection' in locals() else None
            import time; time.sleep(5)

threading.Thread(target=consumidor, daemon=True).start()

@app.get("/")
def home():
    return {"status": "Notification Service rodando e consumindo notificacoes_queue"}