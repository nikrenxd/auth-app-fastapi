from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DB_URL: str

    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_ALGORITHM: str

    JWT_ACCESS_EXPIRE: int
    JWT_REFRESH_EXPIRE: int


settings = Settings()
