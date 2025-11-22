from pydantic import BaseModel
from datetime import date


# Schemas
class ReservaRequest(BaseModel):
    id_hotel: int
    nome_usuario: str
    email_usuario: str
    cep: str
    data_checkin: date
    data_checkout: date
    dias_permanencia: int

class ReservaResponse(BaseModel):
    id: int
    id_hotel: int
    nome_usuario: str
    data_checkin: date
    data_checkout: date
    dias_permanencia: int
    valor_total_reserva: float

    class Config:
        from_attributes = True