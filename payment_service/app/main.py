from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

# Importando do seu projeto
from models import Pagamento, Base
from database import SessionLocal, engine

# Cria a tabela no banco ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Schemas Pydantic ---

# O que o usuário envia para pagar
class PagamentoRequest(BaseModel):
    id_reserva: int
    valor: float
    status: str

# O que a API devolve (inclui o ID gerado pelo banco)
class PagamentoResponse(BaseModel):
    id: int
    id_reserva: int
    valor: float
    status: str

    # Permite ler os dados direto do SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# --- Dependência de Banco ---
def obter_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas ---

@app.post("/pagamentos", response_model=PagamentoResponse)
def realizar_pagamento(pagamento: PagamentoRequest, db: Session = Depends(obter_db)):
    # Cria o objeto do banco
    novo_pagamento = Pagamento(
        id_reserva=pagamento.id_reserva,
        valor=pagamento.valor,
        status=pagamento.status
    )
    
    # Salva no Postgres
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)
    
    return novo_pagamento