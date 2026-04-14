from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "segmentflow"
    POSTGRES_USER: str = "segmentflow"
    POSTGRES_PASSWORD: str = "segmentflow_dev"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # App
    APP_VERSION: str = "0.1.0"
    APP_TITLE: str = "SegmentFlow API"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
