from sqlalchemy import Column, Integer, String, Date,Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    id_hotel = Column(Integer)
    nome_usuario = Column(String)
    email_usuario = Column(String)
    cep = Column(String)
    dias_permanencia = Column(Integer)
    data_checkin = Column(Date)
    data_checkout = Column(Date)
    valor_total_reserva = Column(Numeric(10, 2))