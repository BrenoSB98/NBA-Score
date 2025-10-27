from pydantic import BaseModel, EmailStr, Field

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., example="usuario@exemplo.com")

class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="O token recebido por e-mail")
    new_password: str = Field(..., min_length=8, description="A nova senha (mínimo 8 caracteres)")
    confirm_password: str = Field(..., min_length=8, description="Confirmação da nova senha")