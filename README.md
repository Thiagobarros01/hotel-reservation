# Sistema de Reservas para Hotelaria

## Instalação e Execução

1. Clone o repositório.
2. Certifique-se de que o Docker e Docker Compose estão instalados.
3. No diretório raiz do projeto, execute:
   ```bash
   docker-compose up --build

4. Acesse as APIs:
    Hotel Service: http://localhost:8000/hotels

    Reservation Service: http://localhost:8001/reserve

    Payment Service: http://localhost:8002/payment

5. Acessando http://localhost:8000/docs conseguirá ver a documentação com Swagger.