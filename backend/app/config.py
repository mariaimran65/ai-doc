from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    db_user: str = "aidoc"
    db_password: str = "aidoc"
    db_name: str = "aidoc"
    db_host: str = "db"
    db_port: int = 5432

    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/auth/callback"

    allowed_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
