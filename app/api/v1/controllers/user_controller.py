import logging
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin_user
from app.models.user_models import User
from app.repository import user_repository
from app.schemas import user_schemas, token_schemas
from app.services import email_service

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)
    
@router.get("/verify-email", summary="Verifica o e-mail do usuário usando um token.")
async def verify_email(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de verificação inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.jwt.decode(
            token, security.settings.SECRET_KEY, algorithms=[security.algorithm]
        )
        token_str = token_schemas.TokenData(payload.get("sub"))
        if token_str.email is None:
            raise credentials_exception
    except (security.JWTError, security.ValidationError):
        logger.warning(f"Falha na validação do token de verificação.")
        raise credentials_exception
    
    user = user_repository.user.get_by_email(db, email=token_str.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário para verificação não encontrado."
        )
    if user.is_verified:
        return {"message": "Sua conta já foi verificada anteriormente."}
    
    try:
        user_repository.user.set_user_verified(db, user)
        return {"message": "E-mail verificado com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao verificar e-mail do usuário {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao verificar o e-mail.",
        )

@router.get("/profile", response_model=user_schemas.User, summary="Obtém o perfil do usuário")
def read_user_profile(current_user: User = Depends(get_current_user)):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor, verifique seu e-mail para ativar sua conta."
        )
    return current_user

@router.patch("/profile", response_model=user_schemas.User, summary="Atualiza o perfil do usuário atual")
def update_user_profile(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserUpdate,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor, verifique seu e-mail para ativar sua conta."
        ) 
    user_update_data = user_in.model_dump(exclude_unset=True)
    if not user_update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado fornecido para atualização.",
        )
    
    try:
        updated_user = user_repository.user.update(db, current_user, user_in)
        logger.info(f"Perfil {current_user.email} atualizado com sucesso.")
        return updated_user
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao atualizar o perfil.",
        )

@router.get("/", response_model=List[user_schemas.User], summary="Obtém uma lista de todos os usuários [Admin apenas]")
def read_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_admin_user)):
    if current_user:
        logger.info(f"Admin {current_user.email} solicitou a lista de usuários.")
    users = user_repository.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=user_schemas.User, summary="Obtém detalhes de um usuário por ID [Admin apenas]")
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    if current_user:
        logger.info(f"Admin {current_user.email} solicitou detalhes do usuário ID: {user_id}")
    user = user_repository.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Exclui um usuário por ID [Admin apenas]")
def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    if current_user:
        logger.info(f"Admin {current_user.email} tentou excluir o usuário ID: {user_id}")
    user = user_repository.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins não podem excluir suas próprias contas.",
        )
    try:
        user_repository.user.remove(db, id=user_id)
        logger.info(f"Usuário ID: {user_id} excluído com sucesso pelo admin {current_user.email}.")
    except Exception as e:
        logger.error(f"Erro ao excluir usuário ID: {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao excluir o usuário.",
        )

@router.post("/{user_id}/resend-email-verification", status_code=status.HTTP_202_ACCEPTED, summary="Reenvia o e-mail de verificação para um usuário")
async def resend_email_verification(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = user_repository.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    if user.is_verified:
        return {"message": "A conta deste usuário já foi verificada."}
    
    token_expires = timedelta(minutes=settings.email_verification_token_expire_minutes)
    verify_token = security.create_access_token(user.email, token_expires)
    background_tasks.add_task(email_service.send_verification_email, user.email, verify_token)
    logger.info(f"E-mail de verificação reenviado para o usuário ID: {user_id}.")
    return {"message": "E-mail de verificação reenviado com sucesso."}