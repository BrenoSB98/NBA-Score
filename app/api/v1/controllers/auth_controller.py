import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core import security
from app.core.config import get_settings
from app.repository import user_repository
from app.schemas import token_schemas, user_schemas, password_reset_schemas
from app.services import email_service

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.post("/sign-up", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED, summary="Cria um novo usuário")
async def create_new_user(*, db: Session = Depends(get_db), user_in: user_schemas.UserCreate, background_tasks: BackgroundTasks,):  
    logger.info(f"Criando usuário para: {user_in.email_to_lower}")
    user_existing = user_repository.user.get_by_email(db, email=user_in.email)
    if user_existing:
        logger.warning(f"E-mail já registrado: {user_in.email_to_lower}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este e-mail",
        )
    
    user_cpf = user_repository.user.get_by_cpf(db, cpf=user_in.cpf)
    if user_cpf:
        logger.warning(f"CPF já registrado: {user_in.cpf}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este CPF",
        )
    
    try:
        user = user_repository.user.create(db, obj_in=user_in)
    except Exception as e:
        logger.error(f"Erro ao criar usuário {user_in.email} no banco: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao criar o usuário.",
        )

    token_expires = timedelta(minutes=settings.email_verification_token_expire_minutes)
    verify_token = security.create_access_token(user.email, token_expires)
    background_tasks.add_task(email_service.send_verification_email, user.email, verify_token)
    logger.info(f"Usuário {user.email} criado com sucesso. E-mail de verificação enfileirado.")
    return user

@router.post("/login/access-token", response_model=token_schemas.Token, summary="Obtém um token de acesso JWT")
def login_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Tentativa de login para o usuário: {form_data.username}")
    user = user_repository.user.authenticate(db, email=form_data.username, password=form_data.password)
    
    if not user:
        logger.warning(f"Falha na autenticação para o usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        logger.warning(f"Tentativa de login por usuário inativo: {form_data.username}")
        raise HTTPException(status_code=400, detail="Conta de usuário inativa.")
        
    if not user.is_verified:
        logger.warning(f"Tentativa de login por usuário não verificado: {form_data.username}")
        raise HTTPException(status_code=400, detail="E-mail não verificado.")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    logger.info(f"Login bem-sucedido para o usuário: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/password-rec", status_code=status.HTTP_202_ACCEPTED, summary="Solicita reset de senha")
async def request_password_recovery(request_data: password_reset_schemas.PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = user_repository.user.get_by_email(db, email=request_data.email)

    if not user or not user.is_active:
        logger.warning(f"Tentativa de reset para e-mail não encontrado ou inativo: {request_data.email}")
        return {"message": "Se um usuário com este e-mail existir e estiver ativo, um link de reset será enviado."}
    
    reset_token = security.create_password_reset_token(email=user.email)
    user_repository.user.set_password_reset_token(db=db, user=user, token=reset_token)
    background_tasks.add_task(email_service.send_password_reset_email, user.email, reset_token)
    return {"message": "Se um usuário com este e-mail existir e estiver ativo, um link de reset será enviado."}


@router.post("/reset-password", summary="Define uma nova senha usando o token de reset")
def reset_password(reset_data: password_reset_schemas.PasswordResetConfirm, db: Session = Depends(get_db),):
    email = security.verify_password_reset_token(reset_data.token)
    if not email:
        logger.warning("Token de reset inválido ou expirado fornecido.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de reset inválido ou expirado."
        )
    user = user_repository.user.get_user_by_reset_token(db, token=reset_data.token)
    if not user:
        logger.warning(f"Token válido, mas usuário não encontrado ou token expirado no banco (email: {email}).")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de reset inválido ou expirado." # Mensagem genérica para segurança
        )

    if not user.is_active:
        logger.error(f"Usuário inativo para o token de reset válido (email: {email}).")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuário inativo."
        )
    
    if user.email != email:
         logger.error(f"Discrepância entre e-mail do token ({email}) e usuário encontrado ({user.email}).")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno.")

    try:
        hashed_password = security.get_password_hash(reset_data.new_password)
        user.password_hash = hashed_password
        user_repository.user.clear_password_reset_token(db=db, user=user)
        return {"message": "Senha atualizada com sucesso."}
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao resetar a senha para o usuário {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao atualizar a senha.",
        )