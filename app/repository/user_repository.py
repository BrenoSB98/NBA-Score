from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core import security
from app.models.user_models import User
from app.repository.base_repository import BaseRepository
from app.schemas.user_schemas import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_cpf(self, db: Session, *, cpf: str) -> Optional[User]:
        return db.query(User).filter(User.cpf == cpf).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            date_of_birth=obj_in.date_of_birth,
            cpf=obj_in.cpf,
            password_hash=security.get_password_hash(obj_in.password),
            is_active=True,
            is_verified=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def set_user_verified(self, db: Session, *, email: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if user:
            user.is_verified = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user
    
    def update(db: Session, *, db_obj: User, obj_in: UserUpdate | dict) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = security.get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def set_password_reset_token(self, db: Session, *, user: User, token: str) -> User:
        expires_time = datetime.now(timezone.utc) + timedelta(minutes=security.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        user.password_reset_token = token
        user.password_reset_token_expires = expires_time
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_user_by_reset_token(self, db: Session, *, token: str) -> Optional[User]:
        user = db.query(User).filter(User.password_reset_token == token).first()
        if user and user.password_reset_token_expires and user.password_reset_token_expires > datetime.now(timezone.utc):
            return user
        return None
    
    def clear_password_reset_token(self, db: Session, *, user: User) -> User:
        user.password_reset_token = None
        user.password_reset_token_expires = None
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
user = UserRepository(User)
