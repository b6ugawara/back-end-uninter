from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./database.db"

# Criação da conexão
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Criação das sessões
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para criação dos Models
Base = declarative_base()

# Dependência para acessar o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()