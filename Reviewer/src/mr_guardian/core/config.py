from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    app_name: str = "MR Guardian"
    app_version: str = "0.1.0"
    environment: str = "development"

    llm_provider: str = "ollama"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:latest"

    cloud_enabled: bool = False

    gitlab_url: str = "https://gitlab.com"
    gitlab_api_url: str = "https://gitlab.com/api/v4"
    gitlab_access_token: str | None = None
    gitlab_project_id: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    gitlab_webhook_secret: str | None = None

settings = Settings()