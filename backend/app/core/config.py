"""
Core Application Configuration for EduHyper-RAG FastAPI Backend.
Uses Pydantic Settings with environment variable support, separate development/production
configurations, and strict security guards preventing secret leakage.
"""

import sys
from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure project root is in sys.path so existing 'src' modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class Settings(BaseSettings):
    """Application settings schema backed by environment variables."""

    # Application & Environment
    app_env: str = Field(default="development", description="Environment: development, production, testing")
    app_name: str = Field(default="EduHyper-RAG API", description="Service title")
    app_version: str = Field(default="1.0.0", description="Service semantic version")
    api_prefix: str = Field(default="/api", description="Base API route prefix")

    # Network & Server
    api_host: str = Field(default="127.0.0.1", description="Default bind host")
    api_port: int = Field(default=8000, description="Default bind port")

    # CORS Configuration
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origin URLs for frontend",
    )

    # Project Storage Paths (Reusing existing EduHyperRAG layout)
    project_root: Path = Field(default=PROJECT_ROOT)
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    database_path: Path = Field(default=PROJECT_ROOT / "data" / "eduhyperrag.db")
    knowledge_base_dir: Path = Field(default=PROJECT_ROOT / "data" / "knowledge_base")
    courses_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "courses")

    # Gemini & AI Configuration (Never printed in plain-text logs or responses)
    llm_api_key: Optional[str] = Field(default=None, description="API Key for Google GenAI / Gemini")
    llm_model_name: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")

    # JWT Authentication Configuration
    jwt_secret_key: str = Field(
        default="eduhyperrag-jwt-dev-secret-key-do-not-use-in-production-min32bytes",
        description="Secret key for signing JWT access tokens"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT cryptographic algorithm")
    jwt_access_token_expire_minutes: int = Field(default=1440, description="Token lifespan in minutes")

    # Configuration loading
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "production", "testing"}
        cleaned = value.strip().lower()
        if cleaned not in allowed:
            raise ValueError(f"Invalid APP_ENV: '{value}'. Allowed values are: {', '.join(sorted(allowed))}")
        return cleaned

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            # Split comma-separated string if provided via environment
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    def get_sanitized_config(self) -> dict:
        """Returns non-sensitive metadata for safe health reporting."""
        return {
            "app_name": self.app_name,
            "version": self.app_version,
            "environment": self.app_env,
            "api_prefix": self.api_prefix,
            "model_name": self.llm_model_name,
            "has_llm_key": bool(self.llm_api_key and self.llm_api_key.strip()),
        }


# Global singleton settings instance
settings = Settings()
