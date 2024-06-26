from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    openai_api_token: str
    value_determiner: str
    assistant: str
    model_config = SettingsConfigDict(env_file=".env.gitignore", env_file_encoding="utf-8")


config = Settings()
