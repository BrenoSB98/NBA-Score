# app/services/email_service.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: EmailStr, token: str):
    """Envia um e-mail de verificação de conta para o usuário."""
    verification_url = f"http://localhost:8000/api/v1/users/verify-email?token={token}" 
    
    html = f"""
    <html>
    <body>
        <h1>Verifique seu endereço de e-mail</h1>
        <p>Obrigado por se registrar na Plataforma de Dados NBA! Por favor, clique no link abaixo para verificar seu e-mail e ativar sua conta:</p>
        <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
            Verificar E-mail
        </a>
        <p>Este link expirará em {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutos.</p>
        <p>Se você não se registrou, ignore este e-mail.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Confirmação de Cadastro - Plataforma de Dados NBA",
        recipients=[email],
        body=html,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)