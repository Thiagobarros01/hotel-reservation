from fastapi import FastAPI
import pika
import json
import threading
import asyncio
import os
import aiosmtplib
from email.message import EmailMessage

app = FastAPI(title="Notification Service - E-mail")

# === CONFIGURAÇÃO DE E-MAIL (use Mailtrap pra teste ou Gmail com app password) ===
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "email@email.com"
SMTP_PASS = "pass"  # ← coloca a senha de app do Google

async def enviar_email(dados: dict):
    msg = EmailMessage()
    msg["From"] = f"Hotelaria <{SMTP_USER}>"
    msg["To"] = dados["email_usuario"]
    msg["Subject"] = "Sua reserva foi confirmada! 🎉"

    corpo = f"""
Olá {dados['nome_usuario']},

Sua reserva foi confirmada com sucesso!

Período: de {dados['data_checkin']} até {dados['data_checkout']}
Valor: R$ 350,00

Obrigado por escolher nosso sistema!

Equipe Hotelaria Distribuída 🏨
    """
    msg.set_content(corpo)

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS
        )
        print(f"E-MAIL ENVIADO → {dados['email_usuario']}")
    except Exception as e:
        print(f"ERRO no envio de e-mail: {e}")

# Consumidor com loop assíncrono correto
def start_consumer():
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def callback(ch, method, properties, body):
            dados = json.loads(body)
            print(f"Mensagem recebida → Reserva {dados['id_reserva']} para {dados['nome_usuario']}")
            loop.create_task(enviar_email(dados))
            ch.basic_ack(delivery_tag=method.delivery_tag)

        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.URLParameters("amqp://guest:guest@rabbitmq:5672/")
                )
                channel = connection.channel()
                channel.queue_declare(queue='notificacoes_queue', durable=True)
                channel.basic_consume(queue='notificacoes_queue', on_message_callback=callback)
                print("Notification-service CONECTADO e consumindo fila pagamentos_queue...")
                channel.start_consuming()
            except Exception as e:
                print(f"RabbitMQ desconectado, reconectando em 5s... {e}")
                time.sleep(5)

    threading.Thread(target=run_loop, daemon=True).start()

# Inicia o consumidor ao subir o serviço
start_consumer()

@app.get("/")
def home():
    return {"status": "Notification Service ativo - enviando e-mails automáticos"}