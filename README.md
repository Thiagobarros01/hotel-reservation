# Documentação do Sistema de Reservas de Hotelaria (Microserviços)

Este documento detalha a arquitetura, os componentes e o fluxo de trabalho do sistema de reservas de hotelaria, construído com uma arquitetura de **Microserviços** e orquestrado com **Docker Compose**.

## 1. Arquitetura do Sistema

O projeto adota uma arquitetura de microserviços, onde cada funcionalidade principal é isolada em um serviço independente. A comunicação entre os serviços é realizada de duas formas:

1.  **Comunicação Síncrona (HTTP):** Para consultas diretas (ex: verificar se um hotel existe).
2.  **Comunicação Assíncrona (Message Broker - RabbitMQ):** Para desacoplar processos e garantir que tarefas como pagamento e notificação sejam executadas de forma confiável, mesmo que um serviço esteja temporariamente indisponível.

### Componentes Principais

| Componente | Tecnologia Principal | Porta Exposta | Função |
| :--- | :--- | :--- | :--- |
| **`hotel-service`** | FastAPI (Python), SQLAlchemy | 8000 | Gerencia o cadastro de hotéis e a consulta de CEP (ViaCEP). |
| **`reservation-service`** | FastAPI (Python), SQLAlchemy | 8001 | Cria reservas, consulta o `hotel-service` e envia mensagens para o RabbitMQ. |
| **`payment-service`** | FastAPI (Python), SQLAlchemy | 8002 | Consome mensagens de pagamento do RabbitMQ e simula o processamento. |
| **`notification-service`** | FastAPI (Python), aiosmtplib | 8003 | Consome mensagens de notificação do RabbitMQ e simula o envio de e-mail. |
| **`postgres`** | PostgreSQL 15 | 5555 (Interna 5432) | Banco de dados relacional centralizado para persistência de dados. |
| **`rabbitmq`** | RabbitMQ 3 | 15672 (Web UI), 5672 (AMQP) | Message Broker (fila de mensagens) para comunicação assíncrona. |

## 2. Fluxo de Trabalho da Reserva (Passo a Passo)

O processo de reserva é o coração do sistema e demonstra a comunicação entre os microserviços.

| Passo | Serviço Envolvido | Ação | Explicação para o Professor |
| :--- | :--- | :--- | :--- |
| **1. Início da Reserva** | `reservation-service` | Recebe a requisição POST `/reservas`. | O usuário envia os dados da reserva (hotel, datas, usuário) para a API do serviço de reservas. |
| **2. Validação do Hotel** | `reservation-service` → `hotel-service` | Faz uma chamada HTTP síncrona para o `hotel-service` (porta 8000) para verificar se o `id_hotel` existe. | **Comunicação Síncrona:** Garante a integridade dos dados antes de prosseguir. Se o hotel não for encontrado, a reserva é rejeitada imediatamente. |
| **3. Persistência da Reserva** | `reservation-service` | Salva a nova reserva no banco de dados PostgreSQL. | A reserva é registrada no banco de dados, garantindo que o dado principal da transação seja persistido. |
| **4. Envio para Pagamento** | `reservation-service` → `rabbitmq` | Envia uma mensagem para a fila `pagamentos_queue`. | **Comunicação Assíncrona:** O serviço de reservas não espera pelo pagamento. Ele apenas garante que a mensagem foi entregue ao RabbitMQ, desacoplando o processo. |
| **5. Envio para Notificação** | `reservation-service` → `rabbitmq` | Envia uma mensagem para a fila `notificacoes_queue`. | **Comunicação Assíncrona:** Similar ao pagamento, a notificação é enviada de forma independente, garantindo que o usuário receba a confirmação. |
| **6. Processamento do Pagamento** | `payment-service` | Consome a mensagem da `pagamentos_queue`. | O serviço de pagamento está sempre "escutando" a fila. Ao receber a mensagem, ele simula um processamento (com um `time.sleep(5)` de 5 segundos) e registra o pagamento como "Aprovado" em seu próprio banco de dados. |
| **7. Envio da Notificação** | `notification-service` | Consome a mensagem da `notificacoes_queue`. | O serviço de notificação recebe a mensagem e simula o envio de um e-mail de confirmação para o `email_usuario` usando a biblioteca `aiosmtplib`. |

## 3. Detalhamento dos Microserviços e Arquivos

### 3.1. `hotel-service` (Gerenciamento de Hotéis)

| Arquivo | Função | Detalhes Chave |
| :--- | :--- | :--- |
| `hotel_service/app/main.py` | API Principal | Define as rotas para criar (`POST /hoteis`) e listar (`GET /hoteis`) hotéis. Inclui a rota `/cep/{cep}` que usa a biblioteca `httpx` para consultar a API **ViaCEP** e retornar dados de endereço. |
| `hotel_service/app/models.py` | Modelo de Dados | Define a classe `Hotel` (mapeamento ORM) para a tabela de hotéis no PostgreSQL. |
| `hotel_service/app/schemas.py` | Schemas Pydantic | Define a estrutura dos dados de entrada (`HotelRequest`) e saída (`HotelResponse`), garantindo a validação e serialização dos dados da API. |
| `hotel_service/app/database.py` | Configuração DB | Configura a conexão com o PostgreSQL usando SQLAlchemy, lendo a `DATABASE_URL` das variáveis de ambiente. |

### 3.2. `reservation-service` (Gerenciamento de Reservas)

| Arquivo | Função | Detalhes Chave |
| :--- | :--- | :--- |
| `reservation_service/app/main.py` | API Principal e Produtor RabbitMQ | Rota principal (`POST /reservas`). Após salvar a reserva, utiliza a biblioteca **`pika`** para se conectar ao RabbitMQ e publicar a mesma mensagem em duas filas distintas: `pagamentos_queue` e `notificacoes_queue`. |
| `reservation_service/app/models.py` | Modelo de Dados | Define a classe `Reserva` para a tabela de reservas. |
| `reservation_service/requirements.txt` | Dependências | Lista as bibliotecas necessárias, incluindo `fastapi`, `sqlalchemy`, `pika` (para RabbitMQ) e `httpx` (para chamadas HTTP). |

### 3.3. `payment-service` (Processamento de Pagamento)

| Arquivo | Função | Detalhes Chave |
| :--- | :--- | :--- |
| `payment_service/app/main.py` | API e Consumidor RabbitMQ | Na inicialização (`@app.on_event("startup")`), inicia uma *thread* separada (`iniciar_consumidor`) para escutar a fila `pagamentos_queue`. A função `callback` recebe a mensagem, simula o processamento e registra o pagamento no banco de dados. |
| `payment_service/app/models.py` | Modelo de Dados | Define a classe `Pagamento` para registrar o histórico de pagamentos. |
| **Conceito Chave** | **Consumidor Bloqueante** | O serviço usa `pika.BlockingConnection` e `channel.start_consuming()`, o que significa que ele fica bloqueado esperando por mensagens, sendo o modelo ideal para processamento de tarefas em segundo plano. |

### 3.4. `notification-service` (Envio de Notificações)

| Arquivo | Função | Detalhes Chave |
| :--- | :--- | :--- |
| `notification_service/app/main.py` | API e Consumidor Assíncrono | Inicia uma *thread* para consumir a fila `notificacoes_queue`. O *callback* utiliza **`asyncio`** e **`aiosmtplib`** para simular o envio de e-mails de forma assíncrona, garantindo que o serviço possa lidar com múltiplas notificações rapidamente. |
| **Conceito Chave** | **Desacoplamento** | Este serviço demonstra o valor do RabbitMQ: ele só precisa saber como receber a mensagem da fila, não se importa com quem a enviou (`reservation-service`). |

## 4. Orquestração com Docker Compose

O arquivo `docker-compose.yml` é o "roteiro" que define e executa todos os serviços do sistema.

| Seção do `docker-compose.yml` | Função | Explicação para o Professor |
| :--- | :--- | :--- |
| `services:` | Define cada microserviço. | Cada entrada (`hotel-service`, `postgres`, etc.) é um contêiner isolado. |
| `build: ./<service_name>` | Cria a imagem Docker. | Indica que o Docker deve usar o `Dockerfile` dentro da pasta do serviço para construir a imagem. |
| `ports:` | Mapeamento de Portas. | Exemplo: `"8000:8000"` mapeia a porta 8000 do contêiner para a porta 8000 da máquina host, permitindo acesso externo. |
| `networks: hotelnet` | Rede Interna. | Todos os serviços estão na mesma rede virtual (`hotelnet`), permitindo que se comuniquem usando seus nomes de serviço (ex: `hotel-service:8000`). |
| `depends_on:` | Ordem de Inicialização. | Garante que serviços dependentes (ex: `reservation-service` depende de `postgres` e `rabbitmq`) só iniciem após seus pré-requisitos estarem prontos. O `condition: service_healthy` (para o PostgreSQL) é crucial para garantir que o banco de dados esteja realmente pronto para receber conexões. |
| `environment:` | Variáveis de Ambiente. | Define configurações como a `DATABASE_URL` e a `RABBITMQ_URL`, permitindo que o código se conecte aos outros serviços usando os nomes definidos no `docker-compose.yml`. |
| `healthcheck:` | Verificação de Saúde. | Usado no `postgres` para garantir que o banco de dados esteja totalmente operacional antes que os serviços que dependem dele tentem se conectar. |
| `volumes:` | Persistência de Dados. | O volume `postgres_data` garante que os dados do banco de dados não sejam perdidos quando o contêiner do PostgreSQL for reiniciado. |

## 5. Conceitos de Programação e Tecnologias

| Conceito | Tecnologia/Arquivo | Relevância para o Projeto |
| :--- | :--- | :--- |
| **Framework Web** | FastAPI | Usado para construir APIs de forma rápida e moderna, com documentação automática (Swagger/OpenAPI). |
| **ORM (Mapeamento Objeto-Relacional)** | SQLAlchemy | Permite que o código Python interaja com o banco de dados PostgreSQL usando objetos Python, em vez de SQL puro. |
| **Message Broker** | RabbitMQ (`pika`) | Implementa o padrão **Produtor-Consumidor**, garantindo que as tarefas de pagamento e notificação sejam executadas de forma assíncrona e resiliente. |
| **Comunicação HTTP** | `httpx` | Usado para chamadas síncronas entre serviços (ex: `reservation-service` chamando `hotel-service`). |
| **Serialização/Validação** | Pydantic | Usado para definir os schemas de dados (`Request` e `Response`), garantindo que os dados que entram e saem da API estejam no formato correto. |
| **Contêineres** | Dockerfile | Define o ambiente de execução para cada serviço (instalação de dependências, cópia de código, comando de inicialização), garantindo que o serviço rode de forma idêntica em qualquer ambiente. |
