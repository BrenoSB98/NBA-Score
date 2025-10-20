from pydantic import PostgresDsn, AnyHttpUrl, field_validator, computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union, Any

class Settings(BaseSettings):
    
    # --- Configurações Gerais ---
    project_name: str = "NBA Score API"
    api_v1_str: str = "/api/v1"
    environment: str = "development"
    
    # --- Configurações do Banco de Dados PostgreSQL ---
    postgres_server: str
    postgres_port: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    # --- Configuração do Banco de Dados ---
    @computed_field
    @property
    def database_url(self) -> PostgresDsn:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
    
    # --- Configurações da API de Basquete ---
    nba_api_key: str
    nba_api_host: str = "v2.nba.api-sports.io"
    
    # --- Configurações do Modelo de Linguagem ---
    llm_api_key: Optional[str] = None
    llm_provider_url: Optional[AnyHttpUrl] = None
    llm_model_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    llm_top_p: float = 1.0
    
    # --- Configurações de Segurança ---
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 60 minutos para expiração do token de acesso
    email_verification_token_expire_minutes: int = 1440 # 24 horas para verificação de e-mail

    # --- Validação do Secret Key ---
    @field_validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("A SECRET_KEY deve ter pelo menos 32 caracteres.")
        return v
    
    # --- Configurações do Serviço de E-mail ---
    mail_username: str
    mail_password: str
    mail_from: str
    mail_from_name: str
    mail_port: int
    mail_server: str
    mail_starttls: bool = True
    mail_ssl_tls: bool = False

    # --- CORS (Cross-Origin Resource Sharing) ---
    backend_cors_origins: List[AnyHttpUrl] = []
    
    @field_validator("backend_cors_origins", mode='before')
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith('['):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, list):
            return v
        return []
    
    # --- Configurações do Pydantic V2 ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        alias_generator=lambda field_name: field_name.upper(),
        extra='ignore'
    )

settings = Settings()
