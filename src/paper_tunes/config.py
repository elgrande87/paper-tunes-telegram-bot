from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    work_dir: str = "/data"
    max_file_size_mb: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PT_")
