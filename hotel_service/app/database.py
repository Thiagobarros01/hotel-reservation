from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# URL de conexão com o banco de dados PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/hotelariadb"

# Criar a engine de conexão
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"options": "-c timezone=UTC"})

# Sessão para comunicação com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)