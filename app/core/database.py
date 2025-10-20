import logging
from typing import Generator
from sqlalchemy import create_engine, text, String, Integer, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base(
    type_annotation_map={
        str: String(255),
        int: Integer,
        float: Float,
        bool: Boolean,
    }
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    db: Session | None = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados: {e}")
        return False
    finally:
        if db:
            db.close()
