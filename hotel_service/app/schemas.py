from pydantic import BaseModel 
from decimal import Decimal


# Schemas  -> DTOs in Java

class HotelRequest(BaseModel):
    nome: str
    localizacao: str
    salas_disponiveis: int
    valor_dia: float

class HotelResponse(BaseModel):
    id: int
    nome: str
    localizacao: str
    salas_disponiveis: int
    valor_dia: float

    # Como se fosse o modelMapper do Java
    class Config:
        from_attributes = True

class EnderecoResponse(BaseModel):
    logradouro: str
    bairro: str
    localidade: str
    uf: str