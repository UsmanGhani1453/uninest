from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "UniNest API"
    ENVIRONMENT: str = "local"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGINS: str = "http://localhost:5173"
    MONGODB_URL: str = "mongodb://localhost:27017/uninest?replicaSet=rs0"
    DATABASE_NAME: str = "uninest"
    JWT_SECRET: str = "replace-this-with-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BOOKING_COMMISSION_RATE: float = 0.20
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def frontend_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]


settings = Settings()
