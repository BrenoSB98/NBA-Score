from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import ValidationError
from jose import jwt

from app.core import security
from app.core.config import settings
from app.core.database import get_db

from app.models.user_models import User, UserRole
from app.crud import user_crud
from app.schemas.token_schemas import TokenData

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

def get_current_user(db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenData(**payload)
    except (jwt.JWTError, ValidationError):
        raise credentials_exception
    user = user_crud.get_by_email(db, email=token_data.email)
    
    if not user:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário não tem privilégios suficientes para esta operação."
        )
    return current_user