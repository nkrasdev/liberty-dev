import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/aggregator",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        env="RABBITMQ_URL"
    )
    
    # MinIO
    minio_endpoint: str = Field(
        default="localhost:9000",
        env="MINIO_ENDPOINT"
    )
    minio_access_key: str = Field(
        default="minioadmin",
        env="MINIO_ACCESS_KEY"
    )
    minio_secret_key: str = Field(
        default="minioadmin",
        env="MINIO_SECRET_KEY"
    )
    minio_bucket: str = Field(
        default="aggregator-data",
        env="MINIO_BUCKET"
    )
    minio_secure: bool = Field(
        default=False,
        env="MINIO_SECURE"
    )
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
