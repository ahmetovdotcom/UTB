from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_URL: str
    API_SECRET_KEY: str 

    ADMIN_ID: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()