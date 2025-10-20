from sqlalchemy.orm import Session
from typing import Optional

from app.repository.base_repository import BaseRepository
from app.models.user_models import User
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

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
            password_hash=get_password_hash(obj_in.password),
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
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def update(db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
user = UserRepository(User)
