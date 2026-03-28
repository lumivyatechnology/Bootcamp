"""Application settings using Pydantic Settings for configuration management."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Settings are loaded from environment variables and .env file.
    Environment variables take precedence over .env file values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server settings
    PORT: int = Field(default=3050, description="Port for the FastAPI server")
    HOST: str = Field(default="0.0.0.0", description="Host for the FastAPI server")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    RELOAD: bool = Field(default=True, description="Enable auto-reload for development")

    # Agent settings
    PLANNER_AGENT_TEMPERATURE: float = Field(
        default=0.7, description="Temperature for planner agent"
    )
    TEXT_TO_SQL_AGENT_TEMPERATURE: float = Field(
        default=0.7, description="Temperature for text-to-sql agent"
    )
    OUTPUT_CLASSIFIER_TEMPERATURE: float = Field(
        default=0.0, description="Temperature for output classifier agent"
    )
    REPLANNER_AGENT_TEMPERATURE: float = Field(
        default=1.0, description="Temperature for replanner agent"
    )
    ANSWERS_COMPILER_TEMPERATURE: float = Field(
        default=0.7, description="Temperature for answers compiler agent"
    )

    # Application settings
    APP_NAME: str = Field(default="Analytics Agent", description="Application name")
    APP_VERSION: str = Field(default="0.0.1", description="Application version")

    DATA_BASE_PATH: str = Field(default=".", description="Data base path")
    DATA_BASE_PATH_TEST: str = Field(default=".", description="Data base path")

    LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse secret key")
    LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse public key")
    LANGFUSE_ENVIRONMENT: str = Field(default="", description="Langfuse environment")
    LANGFUSE_BASE_URL: str = Field(default="", description="Langfuse base url")

    GROQ_API_KEY: str = Field(default="", description="Groq API key")

    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int = 5432

    LLM_CONFIG: dict = {}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()


settings = get_settings()

print(settings)
print(settings.LLM_CONFIG)
