from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base


# @Entity annotation equivalent in SQLAlchemy Marcar como entidade JPA
Base = declarative_base()

class Hotel(Base):
    # @Table(name = "hoteis") 	Nome da tabela
    __tablename__ = "hoteis"

    # Column(Integer) @Id     Chave primaria @Index
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    localizacao = Column(String)
    salas_disponiveis = Column(Integer)
    valor_dia = Column(Numeric(10, 2))