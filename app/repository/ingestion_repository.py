import logging
from typing import Type, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.core.database import Base
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def upsert_bulk(
    db: Session,
    model: Type[Base], # type: ignore
    payloads: List[Dict[str, Any]],
    unique_key: str = "source_id"
):
    if not payloads:
        return

    stmt = insert(model).values(payloads)
    
    update_columns = {
        col.name: col
        for col in stmt.excluded
        if col.name not in ["id", unique_key, "created_at"]
    }

    stmt = stmt.on_conflict_do_update(index_elements=[unique_key], set_=update_columns)
    
    result = db.execute(stmt)
    logger.info(f"Upsert para '{model.__tablename__}' concluído. {result.rowcount} linhas afetadas.")
