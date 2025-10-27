import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List

from app.core import security 
from app.core.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: EmailStr, token: str):
    # Exemplo: verification_url = f"http://seu-frontend.com/verify-email?token={token}"
    verification_url = f"http://localhost:8000{settings.api_v1_str}/users/verify-email?token={token}" 
    
    html = f"""
    <html>
    <body>
        <h1>Verifique seu endereço de e-mail</h1>
        <p>Obrigado por se registrar na Plataforma de Dados NBA! Por favor, clique no link abaixo para verificar seu e-mail e ativar sua conta:</p>
        <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
            Verificar E-mail
        </a>
        <p>Este link expirará em {settings.email_verification_token_expire_minutes // 60} horas.</p> 
        <p>Se você não se registrou, por favor ignore este e-mail.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Verificação de E-mail - NBA SCORE",
        recipients=[email],
        body=html,
        subtype="html",
        sender=(settings.mail_from_name, settings.mail_from)
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        logging.info(f"E-mail de verificação enviado para {email}")
    except Exception as e:
        logging.error(f"Falha ao enviar e-mail de verificação para {email}: {e}")

async def send_password_reset_email(email: EmailStr, token: str):
    # Exemplo: reset_url = f"http://seu-frontend.com/reset-password?token={token}"
    reset_url = f"http://localhost:8000{settings.api_v1_str}/auth/reset-password-form?token={token}"

    html = f"""
    <html>
    <body>
        <h1>Reset da sua Senha</h1>
        <p>Você solicitou um reset de senha. Clique no link abaixo para definir uma nova senha:</p>
        <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #ffc107; color: black; text-decoration: none; border-radius: 5px;">
            Resetar Senha
        </a>
        <p>Este link expirará em {security.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos.</p> 
        <p>Se você não solicitou este reset, por favor ignore este e-mail.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Reset de Senha - NBA SCORE",
        recipients=[email],
        body=html,
        subtype="html",
        sender=(settings.mail_from_name, settings.mail_from)
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        logging.info(f"E-mail de reset de senha enviado para {email}")
    except Exception as e:
        logging.error(f"Falha ao enviar e-mail de reset para {email}: {e}")
