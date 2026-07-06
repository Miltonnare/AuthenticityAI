from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "Authenticity AI Platform"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql://dev_user:dev_secure_password@localhost:5432/authenticity"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    JWT_SECRET: str = "super_secret_jwt_key_authenticity_platform_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

settings = Settings()
