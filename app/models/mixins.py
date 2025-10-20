from sqlalchemy import Column, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from datetime import datetime
from typing import Annotated

timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.now())
]

class TimestampMixin:
    created_at: Mapped[timestamp]
    updated_at: Mapped[Annotated[
        datetime,
        mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
    ]]

class IngestionControlMixin:
    source_id = Column(Integer, nullable=False, comment="ID original da fonte de dados externa (API)")
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    payload_hash = Column(String(64), nullable=False, comment="Hash SHA-256 do payload da API para detecção de mudanças")
    is_active = Column(Integer, default=1, nullable=False, comment="Indica se o registro está ativo (1) ou inativo (0)")
