from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional
from validate_docbr import CPF

from app.models.user_models import UserRole

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="exemple@example.com")
    full_name: str = Field(..., min_length=8, example="Pedro Balafina")
    date_of_birth: date | str = Field(..., example="12/10/1998") # Formato brasileiro DD/MM/YYYY

class UserCreate(UserBase):
    cpf: str = Field(..., example="12345678900")
    password: str = Field(..., min_length=10, description="A senha deve ter no mínimo 10 caracteres")

    @field_validator('email')
    def email_to_lower(cls, v: str) -> str:
        return v.lower()

    @field_validator('date_of_birth', mode='before')
    def parse_date_of_birth(cls, v: str) -> date:
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%d/%m/%Y').date()
            except ValueError:
                raise ValueError("Formato de data inválido. Use DD/MM/YYYY.")
        return v

    @field_validator('cpf')
    def validate_and_clean_cpf(cls, v: str) -> str:
        cpf_validator = CPF()
        if not cpf_validator.validate(v):
            raise ValueError('CPF fornecido é inválido.')
        return cpf_validator.get_digits(v)

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=8, example="Pedro Balafina Nogueira")
    date_of_birth: Optional[date | str] = Field(None, example="12/10/1999")
    password: Optional[str] = Field(None, min_length=10, description="A senha deve ter no mínimo 10 caracteres")

    class Config:
        validate_assignment = True

    @field_validator('date_of_birth', mode='before')
    def parse_update_date_of_birth(cls, v: Optional[str]) -> Optional[date]:
        if v is None:
            return None
        return UserCreate.parse_date_of_birth(v)

class User(UserBase):
    id: int
    cpf: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class UserInDB(User):
    hashed_password: str
