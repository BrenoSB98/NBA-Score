from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging

from app.core.database import check_db_connection
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.get("/verify", status_code=status.HTTP_200_OK, summary="Verifica a saúde da aplicação")
def verify_db_check() -> dict:
    db_ok = check_db_connection()
    
    if db_ok:
        return {"status": "ok", "database_connection": "ok"}
    else:
        logger.warning("A verificação detectou falha na conexão com o banco de dados.")
        return {"status": "ok", "database_connection": "error"}

@router.get("/ping", status_code=status.HTTP_200_OK, summary="Endpoint simples para teste de conectividade")
def ping() -> dict:
    return {"ping": "pong"}