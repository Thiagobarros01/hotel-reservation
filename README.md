# Sistema de Reservas de Hotelaria - Microserviços com FastAPI + Docker

## Arquitetura (atende todos os requisitos da avaliação)

- 3 Microserviços:
  - `hotel-service`: Cadastro e consulta de hotéis
  - `reservation_service`: Criação de reservas + ViaCEP (API externa)
  - `payment-service`: Processamento assíncrono de pagamentos via RabbitMQ

- Comunicação síncrona: reservation_service → hotel_service (HTTP)
- Comunicação assíncrona: reservation_service → payment-service (RabbitMQ)
- API externa: ViaCEP (preenche endereço automaticamente)
- Documentação: Swagger/OpenAPI em /docs de cada serviço
- Orquestração: Docker Compose + PostgreSQL + RabbitMQ

## Como rodar

```bash
docker compose up --build