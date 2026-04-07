from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    POSTGRES_USER: str = "vault_user"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "evidencevault"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # MinIO
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "changeme"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_BUCKET: str = "evidence"
    MINIO_SECURE: bool = False

    # JWT
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Dev flags
    DEV_BOOTSTRAP_ENABLED: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
