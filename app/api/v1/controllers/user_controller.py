from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.repository import user_repository
from app.models.user_models import User
from app.schemas import user_schemas
from app.core import security
from app.core.config import settings
from app.services import email_service

router = APIRouter()

@router.post("/", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate,
    background_tasks: BackgroundTasks,
):
    """
    Cria um novo usuário, valida CPF e e-mail, e envia e-mail de verificação.
    """
    if user_repository.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este e-mail no sistema.",
        )
    if user_repository.get_by_cpf(db, cpf=user_in.cpf):
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este CPF no sistema.",
        )
        
    user = user_repository.create(db, user_in=user_in)
    
    # Enviar e-mail de verificação em segundo plano
    token_expires = timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    verification_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=token_expires
    )
    background_tasks.add_task(
        email_service.send_verification_email, email=user.email, token=verification_token
    )
    
    return user

@router.get("/verify-email", summary="Verifica o e-mail do usuário usando um token.")
async def verify_email_endpoint(token: str, db: Session = Depends(get_db)):
    """
    Endpoint que recebe o token do e-mail para confirmar o cadastro do usuário.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de verificação inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.jwt.decode(
            token, security.settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except security.JWTError:
        raise credentials_exception
    
    user = user_repository.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário para verificação não encontrado.")
    if user.is_verified:
        return {"message": "Sua conta já foi verificada anteriormente."}
    
    user_repository.set_user_verified(db, email=email)
    return {"message": "E-mail verificado com sucesso! Você já pode fazer o login."}


@router.get("/me", response_model=user_schemas.User)
def read_user_me(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os dados do usuário atualmente logado.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor, verifique seu e-mail para ativar sua conta."
        )
    return current_user