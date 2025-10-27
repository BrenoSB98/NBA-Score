from fastapi import APIRouter

from .controllers import user_controller, auth_controller, ingestion_controller, verify_connection

api_router = APIRouter()

api_router.include_router(verify_connection.router, prefix="/verify", tags=["Verify Connection"])
api_router.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user_controller.router, prefix="/users", tags=["Users"])
api_router.include_router(ingestion_controller.router, prefix="/admin", tags=["Admin"])

@api_router.get("/ping")
def ping():
    return {"ping": "pong"}