import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.api import api_router
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cria as tabelas no banco de dados (Apenas para desenvolvimento/teste)
# Em produção, as migrações Alembic devem ser usadas
# logger.info("Verificando/Criando tabelas do banco de dados (desabilitado, use Alembic)...")
# try:
#     # Base.metadata.create_all(bind=engine) # Comentado para usar Alembic
#     logger.info("Criação de tabelas via create_all desabilitada. Use 'alembic upgrade head'.")
# except Exception as e:
#     logger.error(f"Erro ao verificar tabelas (create_all comentado): {e}")
    # Considerar levantar a exceção ou sair se a criação for crítica

# Carrega as configurações
settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    version="0.1.0"
)

if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS habilitado para as origens: {settings.backend_cors_origins}")
else:
    logger.info("CORS não configurado (nenhuma origem definida em BACKEND_CORS_ORIGINS).")

app.include_router(api_router, prefix=settings.api_v1_str)

@app.get("/", summary="Endpoint raiz para verificação de status")
def read_root():
    """
    Endpoint de health check básico para verificar se a API está online.
    """
    return {"status": "ok", "project_name": settings.project_name}

logger.info(f"Aplicação FastAPI '{settings.project_name}' inicializada.")

if __name__ == "__main__":
    import uvicorn
    port = getattr(settings, "PORT", 8000)
    reload = settings.environment == "development"
    log_level = "info" if settings.environment == "production" else "debug"
    debug_mode = reload

    logger.info(f"Iniciando Uvicorn...")
    uvicorn.run(app="main:app",host="0.0.0.0", port=8000, reload=reload, log_level=log_level.lower(),)